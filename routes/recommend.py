from flask import Blueprint, request, jsonify
import json, re, time

from services.shared import groq_client as client

recommend_bp = Blueprint("recommend", __name__)


# =========================
# Load Prompt
# =========================
def load_prompt():
    try:
        with open("prompts/recommend_prompt.txt", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return """
You are a healthcare assistant.

Patient Data:
{text}

Give medical recommendations in JSON ARRAY.

STRICT RULES:
- Return ONLY JSON ARRAY
- No explanation outside JSON

FORMAT:
[
  {
    "action": "Consult Doctor",
    "description": "Reason",
    "priority": "HIGH/MEDIUM/LOW"
  }
]
"""


PROMPT = load_prompt()


# =========================
# ROUTE
# =========================
@recommend_bp.route("/recommend", methods=["POST"])
def recommend():
    """
    Generate health recommendations using AI
    ---
    tags:
      - Health Recommend

    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            text:
              type: string
              example: Patient has fever, cough, oxygen level 90%

    responses:
      200:
        description: Health recommendations
    """

    try:
        # ✅ safe JSON
        data = request.get_json(silent=True)

        if not data or "text" not in data:
            return jsonify({
                "error": "Missing 'text' field",
                "example": {
                    "text": "Patient has fever and cough"
                }
            }), 400

        text = data["text"]

        # 🔹 prompt
        prompt = PROMPT.replace("{text}", text)

        start = time.time()

        # ✅ correct call
        response = client.generate(prompt)

        end = time.time()

        print("🧠 RAW RESPONSE:", response)

        # =========================
        # JSON PARSE
        # =========================
        try:
            match = re.search(r'\[[\s\S]*\]', response)

            if match:
                parsed = json.loads(match.group())
            else:
                raise ValueError("No JSON")

        except:
            parsed = [
                {
                    "action": "Monitor symptoms",
                    "description": "Unable to parse AI response",
                    "priority": "LOW"
                }
            ]

        return jsonify({
            "data": parsed,
            "meta": {
                "model_used": getattr(client, "model", "unknown"),
                "response_time_ms": int((end - start) * 1000)
            }
        }), 200

    except Exception as e:
        print("❌ Recommend error:", e)

        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500