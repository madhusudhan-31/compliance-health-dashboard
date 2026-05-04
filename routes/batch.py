from flask import Blueprint, request, jsonify
import time, json, re

from services.shared import groq_client as client

batch_bp = Blueprint("batch", __name__)


# =========================
# Load prompt
# =========================
def load_prompt():
    try:
        with open("prompts/describe_prompt.txt") as f:
            return f.read()
    except:
        return "Analyze health risk for: {text} and return JSON"


PROMPT = load_prompt()


# =========================
# ROUTE
# =========================
@batch_bp.route("/batch", methods=["POST"])
def batch():
    """
    Batch health risk analysis
    ---
    tags:
      - Health Batch

    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            items:
              type: array
              items:
                type: string
              example:
                - Patient has fever and cough
                - Oxygen level dropped to 88%

    responses:
      200:
        description: Batch health analysis results
    """

    try:
        # ✅ Get JSON safely
        data = request.get_json(silent=True)

        if not data or "items" not in data:
            return jsonify({
                "error": "Missing 'items' field",
                "example": {
                    "items": [
                        "Patient has fever",
                        "Oxygen level 88%"
                    ]
                }
            }), 400

        items = data["items"]

        start_time = time.time()
        results = []

        # =========================
        # PROCESS EACH ITEM
        # =========================
        for item in items:
            item_start = time.time()

            try:
                prompt = PROMPT.replace("{text}", item)

                # 🔹 AI response per item
                response = client.generate(prompt)

                # 🔹 Extract JSON safely
                json_match = re.search(r'\{[\s\S]*\}', response)

                if json_match:
                    parsed = json.loads(json_match.group())
                else:
                    parsed = {
                        "health_risk_level": "Unknown",
                        "explanation": "Invalid AI response",
                        "key_indicators": []
                    }

            except Exception as e:
                print("❌ Batch item error:", e)

                parsed = {
                    "health_risk_level": "Error",
                    "explanation": "Processing failed",
                    "key_indicators": []
                }

            item_end = time.time()

            results.append({
                "input": item,
                "output": parsed,
                "meta": {
                    "response_time_ms": int((item_end - item_start) * 1000)
                }
            })

        end_time = time.time()

        # =========================
        # 🔥 AI SUMMARY (ALL ITEMS)
        # =========================
        try:
            combined_text = "\n".join(items)

            ai_summary_prompt = f"""
You are a healthcare assistant.

Analyze the following patient cases:

{combined_text}

Give:
- Overall health summary
- Major risks
- General advice
"""

            ai_response = client.generate(ai_summary_prompt)

        except Exception as e:
            print("❌ AI summary error:", e)
            ai_response = "AI summary unavailable"

        # =========================
        # RESPONSE
        # =========================
        return jsonify({
            "results": results,
            "ai_response": ai_response,
            "meta": {
                "total_items": len(results),
                "total_time_ms": int((end_time - start_time) * 1000),
                "model_used": getattr(client, "model", "unknown")
            }
        }), 200

    except Exception as e:
        print("❌ Batch API error:", e)

        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500