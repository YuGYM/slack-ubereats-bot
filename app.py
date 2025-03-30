from flask import Flask, request, jsonify
import requests
import random
import os

app = Flask(__name__)

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

# ➤ 取得經緯度，帶完整錯誤處理
def get_location_coordinates(location_name):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": location_name,
        "key": GOOGLE_API_KEY,
        "language": "zh-TW"
    }

    print("👉 使用的地名：", location_name)
    print("👉 API KEY（部分）：", GOOGLE_API_KEY[:8] + "******")

    try:
        res = requests.get(url, params=params)
        data = res.json()

        print("📦 Geocoding 回傳資料：", data)

        if data.get("status") != "OK":
            print("❌ Geocode status 不是 OK：", data.get("status"))
            return None, None

        results = data.get("results")
        if not results or len(results) == 0:
            print("❌ Geocode 沒有 results")
            return None, None

        geometry = results[0].get("geometry")
        if not geometry:
            print("❌ geometry 欄位為 None")
            return None, None

        location = geometry.get("location")
        if not location:
            print("❌ location 欄位為 None")
            return None, None

        lat = location.get("lat")
        lng = location.get("lng")
        if lat is None or lng is None:
            print("❌ lat/lng 為 None")
            return None, None

        print(f"✅ 取得經緯度：lat={lat}, lng={lng}")
        return lat, lng

    except Exception as e:
        print("❗ Geocode 發生錯誤：", str(e))
        return None, None


# ➤ Google Places API 拿附近餐廳
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


# ➤ Slack Bot Entry Point
@app.route("/ubereats", methods=["POST"])
def ubereats():
    try:
        text = request.form.get("text", "").strip()
        user_id = request.form.get("user_id", "")

        print(f"👤 使用者 <@{user_id}> 查詢：{text}")

        if not text:
            return jsonify({"text": "請輸入地點，例如 `/ubereats 台北101`"})

        lat, lng = get_location_coordinates(text)
        if lat is None or lng is None:
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
        print("❗ 主流程錯誤：", str(e))
        return jsonify({"text": "⚠️ 程式錯誤，請稍後再試"}), 500


@app.route("/")
def hello():
    return "Ubereats bot with Google Maps is running!"

if __name__ == "__main__":
    app.run()
