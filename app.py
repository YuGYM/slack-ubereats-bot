from flask import Flask, request, jsonify
import requests
import random
import os

app = Flask(__name__)

# 讀取 Google Maps API 金鑰（從環境變數）
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")


# ➤ 將地點文字轉換成經緯度
def get_location_coordinates(location_name):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": location_name,
        "key": GOOGLE_API_KEY,
        "language": "zh-TW"
    }

    print("👉 使用的地名：", location_name)
    print("👉 使用的 API KEY（部分）：", GOOGLE_API_KEY[:8] + "******")

    res = requests.get(url, params=params)
    data = res.json()

    print("📦 Geocoding 回傳資料：", data)

    if data["status"] == "OK":
        location = data["results"][0]["geometry"]["location"]
        return location["lat"], location["lng"]
    else:
        print("Geocode failed:", data)
        return None, None


# ➤ 取得地點附近的餐廳清單
def get_nearby_restaurants(lat, lng):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": 1000,
        "type": "restaurant",
        "language": "zh-TW",
        "key": GOOGLE_API_KEY
    }

    res = requests.get(url, params=params)
    data = res.json()

    print("📦 Places 回傳資料：", data)

    restaurants = data.get("results", [])
    return restaurants


# ➤ Slack Slash Command Endpoint
@app.route("/ubereats", methods=["POST"])
def ubereats():
    try:
        text = request.form.get("text", "").strip()
        user_id = request.form.get("user_id", "")

        print(f"👤 來自 Slack 使用者 <@{user_id}> 查詢：{text}")

        if not text:
            return jsonify({"text": "請輸入地點，例如 `/ubereats 台北101`"})

        lat, lng = get_location_coordinates(text)
        if lat is None:
            return jsonify({"text": f"❌ 找不到「{text}」，請確認地點是否正確"})

        restaurants = get_nearby_restaurants(lat, lng)
        if not restaurants:
            return jsonify({"text": "😓 找不到附近餐廳，可能是地點太偏僻？"})

        pick = random.choice(restaurants)
        name = pick.get("name", "未知店名")
        address = pick.get("vicinity", "地址不明")
        rating = pick.get("rating", "無評分")
        link = f"https://www.google.com/maps/search/?api=1&query={name.replace(' ', '+')}"

        return jsonify({
            "text": f"🍽️ <@{user_id}> 我推薦你吃：*{name}*\n📍 {address}\n⭐ 評分：{rating}\n🔗 [看地圖]({link})"
        })

    except Exception as e:
        print("❗ 程式錯誤：", str(e))
        return jsonify({"text": "⚠️ 程式錯誤，請稍後再試（log 中已輸出錯誤）"}), 500


# ➤ Render Home 頁面測試用
@app.route("/")
def hello():
    return "Ubereats bot with Google Maps is running!"

if __name__ == "__main__":
    app.run()
