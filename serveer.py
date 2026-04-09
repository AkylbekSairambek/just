from flask import Flask, request, jsonify
from openai import OpenAI
from flask_cors import CORS
from dotenv import load_dotenv
import json
import os

app = Flask(__name__)
load_dotenv()
CORS(app)


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/ask", methods=["POST"])
def ask_gpt():
    data = request.get_json()
    user_question = data.get("question", "")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": user_question}]
    )

    answer = response.choices[0].message.content
    return jsonify({"answer": answer})


# Загружаем локации из JSON
with open("locations.json", "r", encoding="utf-8") as f:
    LOCATIONS = json.load(f)

@app.route("/locations", methods=["GET"])
def get_locations():
    """Фильтрация локаций по типу отдыха и бюджету"""
    loc_type = request.args.get("type")  # например 'горы'
    max_budget = request.args.get("budget", type=int)

    filtered = LOCATIONS
    if loc_type:
        filtered = [l for l in filtered if l["type"] == loc_type]

    if max_budget:
        def estimate_cost(l, days=3):
            return l["accom"]*days + l["food"]*days + l["transport"] + l["activities"]
        filtered = [l for l in filtered if estimate_cost(l) <= max_budget]

    return jsonify(filtered)

@app.route("/estimate", methods=["POST"])
def estimate_budget():
    """Расчёт бюджета для выбранной локации"""
    data = request.json
    loc_id = data.get("location_id")
    days = int(data.get("days", 3))
    people = int(data.get("people", 1))
    contingency = float(data.get("contingency_pct", 10))

    loc = next((l for l in LOCATIONS if l["id"] == loc_id), None)
    if not loc:
        return jsonify({"error": "Локация не найдена"}), 404

    accom_total = loc["accom"] * days * people
    food_total = loc["food"] * days * people
    transport_total = loc["transport"] * people
    activities_total = loc["activities"] * people
    subtotal = accom_total + food_total + transport_total + activities_total
    contingency_sum = subtotal * (contingency / 100)
    total = subtotal + contingency_sum

    return jsonify({
        "location": loc["name"],
        "breakdown": {
        "accom": accom_total,
        "food": food_total,
        "transport": transport_total,
        "activities": activities_total,
        "contingency": contingency_sum
        },
        "total": total
    })

if __name__ == "__main__":
    app.run(debug=True)
