from flask import Flask, request, jsonify
import requests
import random
import os

app = Flask(__name__)

# 從環境變數取得 Google Maps API 金鑰
GOOGLE_API_KEY = os.environ.get("AIzaSyACEeojcbZgXusHmjI3uiHNsPoPwqDmveA")


# 🔍 Step 1: 透過地名取得經緯度
def get_location_coordinates(location_name):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": location_name,
        "key": GOOGLE_API_KEY,
        "language": "zh-TW"
    }

    res = requests.get(url, params=params)
    data = res.json()

    if data["status"] == "OK":
        location = data["results"][0]["geometry"]["location"]
        return location["lat"], location["lng"]
    else:
        print("Geocode failed:", data)
        return None, None


# 🍱 Step 2: 用經緯度取得附近餐廳
def get_nearby_restaurants(lat, lng):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": 1000,  # 公尺
        "type": "restaurant",
        "language": "zh-TW",
        "key": GOOGLE_API_KEY
    }

    res = requests.get(url, params=params)
    data = res.json()
    restaurants = data.get("results", [])

    return restaurants


# 📡 Step 3: Slack 呼叫的 Endpoint
@app.route("/ubereats", methods=["POST"])
def ubereats():
    text = request.form.get("text", "")
    user_id = request.form.get("user_id", "")

    if not text:
        return jsonify({"text": "請輸入地點，例如 `/ubereats 台北101`"})

    lat, lng = get_location_coordinates(text)
    if lat is None:
        return jsonify({"text": "❌ 找不到這個地點，請確認輸入的地名"})

    restaurants = get_nearby_restaurants(lat, lng)
    if not restaurants:
        return jsonify({"text": "😓 找不到餐廳，請稍後再試"})

    pick = random.choice(restaurants)
    name = pick["name"]
    address = pick.get("vicinity", "地址不明")
    rating = pick.get("rating", "無評分")
    link = f"https://www.google.com/maps/search/?api=1&query={name.replace(' ', '+')}"

    return jsonify({
        "text": f"🍽️ <@{user_id}>，我推薦你吃：*{name}*！\n📍 {address}\n⭐ 評分：{rating}\n🔗 [看地圖]({link})"
    })


# ✅ Render 測試首頁
@app.route("/")
def hello():
    return "Ubereats bot with Google Maps is running!"

if __name__ == "__main__":
    app.run()
