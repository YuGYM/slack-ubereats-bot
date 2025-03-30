from flask import Flask, request, jsonify
import requests
import random
import os

app = Flask(__name__)

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

@app.route("/")
def hello():
    return "✅ Ubereats bot with Google Maps is running!"

# ➤ 將地名轉成經緯度
def get_location_coordinates(location_name):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": location_name,
        "key": GOOGLE_API_KEY,
        "language": "zh-TW"
    }

    print("🧪 版本標記：2025-03-30 最終防呆版")
    print("👉 使用的地名：", location_name)

    try:
        res = requests.get(url, params=params)
        data = res.json()
        print("📦 Geocoding 回傳資料：", data)

        if data.get("status") != "OK":
            print("❌ Geocode status 非 OK：", data.get("status"))
            return None, None

        results = data.get("results")
        if not results or len(results) == 0:
            print("❌ Geocode 無 results")
            return None, None

        geometry = results[0].get("geometry")
        if not geometry:
            print("❌ Geocode geometry 為 None")
            return None, None

        location = geometry.get("location")
        if not location:
            print("❌ Geocode location 為 None")
            return None, None

        lat = location.get("lat")
        lng = location.get("lng")

        print(f"✅ 經緯度：lat={lat}, lng={lng}")
        return lat, lng

    except Exception as e:
        print("❗ Geocode 發生錯誤：", str(e))
        return None, None

# ➤ 查詢附近餐廳
def get_nearby_restaurants(lat, lng):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": 1000,
        "type": "restaurant",
        "language": "zh-TW",
        "key": GOOGLE_API_KEY
    }

    try:
        res = requests.get(url, params=params)
        data = res.json()
        print("📦 Places 回傳資料：", data)

        restaurants = data.get("results", [])
        return restaurants
    except Exception as e:
        print("❗ Places 錯誤：", str(e))
        return []

# ➤ Slack Slash Command 入口
@app.route("/ubereats", methods=["POST"])
def ubereats():
    try:
        text = request.form.get("text", "").strip()
        user_id = request.form.get("user_id", "")

        print(f"👤 Slack 使用者 <@{user_id}> 查詢地點：{text}")

        if not text:
            return jsonify({"text": "請輸入地點，例如 `/ubereats 台北101`"})

        lat, lng = get_location_coordinates(text)
        if lat is None or lng is None:
            return jsonify({"text": f"❌ 找不到「{text}」，請確認地點是否正確"})

        restaurants = get_nearby_restaurants(lat, lng)
        if not restaurants:
            return jsonify({"text": "😓 找不到附近餐廳，可能是地點太偏僻？"})

        # 過濾掉沒有名稱的資料，避免取用 None
        valid_restaurants = [r for r in restaurants if r and r.get("name")]
        if not valid_restaurants:
            return jsonify({"text": "😓 找不到有效餐廳（沒有名稱），請稍後再試"})

        pick = random.choice(valid_restaurants)
        name = pick.get("name", "未知店名")
        address = pick.get("vicinity", "地址不明")
        rating = pick.get("rating", "無評分")
        link = f"https://www.google.com/maps/search/?api=1&query={name.replace(' ', '+')}"

        return jsonify({
            "text": f"🍽️ <@{user_id}> 我推薦你吃：*{name}*\n📍 {address}\n⭐ 評分：{rating}\n🔗 [看地圖]({link})"
        })

    except Exception as e:
        print("❗ 主流程錯誤：", str(e))
        return jsonify({"text": "⚠️ 程式錯誤，請稍後再試"}), 500

if __name__ == "__main__":
    app.run()
