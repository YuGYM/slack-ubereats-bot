from flask import Flask, request, jsonify
import requests
import random
import os

app = Flask(__name__)

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

@app.route("/")
def hello():
    return "✅ Ubereats bot with Google Maps is running!"


def get_location_coordinates(location_name):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": location_name,
        "key": GOOGLE_API_KEY,
        "language": "zh-TW"
    }

    print("🧪 版本：含圖片")
    print("👉 查詢地點：", location_name)

    try:
        res = requests.get(url, params=params)
        data = res.json()
        print("📦 Geocoding 回傳：", data)

        if data.get("status") != "OK":
            return None, None

        location = data["results"][0].get("geometry", {}).get("location")
        if not location:
            return None, None

        return location.get("lat"), location.get("lng")

    except Exception as e:
        print("❗ Geocode 錯誤：", str(e))
        return None, None


def get_nearby_restaurants(lat, lng):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": 5000,
        "type": "restaurant",
        "language": "zh-TW",
        "key": GOOGLE_API_KEY
    }

    try:
        res = requests.get(url, params=params)
        data = res.json()
        print("📦 Places 回傳：", data)
        return data.get("results", [])
    except Exception as e:
        print("❗ Places 錯誤：", str(e))
        return []


@app.route("/ubereats", methods=["POST"])
def ubereats():
    try:
        text = request.form.get("text", "").strip()
        user_id = request.form.get("user_id", "")

        if not text:
            return jsonify({"text": "請輸入地點，例如 `/ubereats 台北101 3`"})

        parts = text.rsplit(" ", 1)
        location_name = parts[0]
        count = 1

        if len(parts) == 2 and parts[1].isdigit():
            count = int(parts[1])

        lat, lng = get_location_coordinates(location_name)
        if lat is None or lng is None:
            return jsonify({"text": f"❌ 找不到「{location_name}」，請確認地點是否正確"})

        restaurants = get_nearby_restaurants(lat, lng)
        if not restaurants:
            return jsonify({"text": "😓 找不到附近餐廳，可能是地點太偏僻？"})

        filtered = [
            r for r in restaurants
            if r.get("name") and r.get("rating", 0) >= 4.2
        ]

        if not filtered:
            return jsonify({"text": "😓 找不到評分 4.2 分以上的餐廳，請換個地點試試！"})

        random.shuffle(filtered)
        picks = filtered[:min(count, len(filtered))]

        messages = []
        for i, pick in enumerate(picks, start=1):
            name = pick.get("name", "未知店名")
            address = pick.get("vicinity", "地址不明")
            rating = pick.get("rating", "無評分")

            # ➤ 處理圖片
            photo_ref = pick.get("photos", [{}])[0].get("photo_reference")
            if photo_ref:
                photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photo_reference={photo_ref}&key={GOOGLE_API_KEY}"
            else:
                photo_url = "https://via.placeholder.com/400x300?text=No+Image"

            # ➤ Google Maps 查詢連結
            link = f"https://www.google.com/maps/search/?api=1&query={name.replace(' ', '+')}"

            messages.append(
                f"*{i}. {name}*\n📍 {address}\n⭐ 評分：{rating}\n🔗 {link}\n🖼️ {photo_url}"
            )

        reply = f"🍽️ <@{user_id}> 推薦你在「{location_name}」附近的餐廳（評分4.2↑）：\n\n" + "\n\n".join(messages)

        return jsonify({
            "response_type": "in_channel",
            "text": reply
        })

    except Exception as e:
        print("❗ 主程式錯誤：", str(e))
        return jsonify({"text": "⚠️ 程式錯誤，請稍後再試"}), 500


if __name__ == "__main__":
    app.run()
