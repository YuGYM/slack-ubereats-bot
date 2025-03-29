from flask import Flask, request, jsonify
import requests
import random

app = Flask(__name__)

LATITUDE = 25.0478
LONGITUDE = 121.5319

HEADERS = {
    "accept": "application/json",
    "user-agent": "UberEats/6.102.10001 (iPhone; iOS 14.4; Scale/2.00)"
}

def get_restaurants(lat, lng):
    url = "https://www.ubereats.com/_p/api/getFeedV1?localeCode=zh-TW"
    payload = {
        "marketId": "",
        "storeFrontId": None,
        "userDeviceLatLng": {"latitude": lat, "longitude": lng},
        "supportedEaterFeatures": [],
    }

    try:
        res = requests.post(url, json=payload, headers=HEADERS)
        data = res.json()
        items = data.get("data", {}).get("feedItems", [])
        restaurants = [
            item["store"]["title"]
            for item in items
            if item.get("type") == "store"
        ]
        return restaurants
    except Exception as e:
        print("Error fetching restaurants:", e)
        return []

@app.route("/ubereats", methods=["POST"])
def ubereats():
    text = request.form.get("text")
    user_id = request.form.get("user_id")

    restaurants = get_restaurants(LATITUDE, LONGITUDE)

    if not restaurants:
        return jsonify({"text": "😓 找不到餐廳，請稍後再試"})

    choice = random.choice(restaurants)
    return jsonify({"text": f"🍽️ <@{user_id}>，我推薦你吃：*{choice}*"})


@app.route("/")
def hello():
    return "Ubereats bot is running!"

if __name__ == "__main__":
    app.run()
