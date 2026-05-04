from flask import Blueprint, request, jsonify
import time

from services.shared import groq_client as client

categorise_bp = Blueprint("categorise", __name__)


@categorise_bp.route("/categorise", methods=["POST"])
def categorise():
    """
    Health Categorisation API
    ---
    tags:
      - Health Categorise

    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            text:
              type: string
              example: Patient has chest pain and shortness of breath

    responses:
      200:
        description: Success
    """

    try:
        data = request.get_json(silent=True)

        if not data or "text" not in data:
            return jsonify({"error": "text required"}), 400

        text = data["text"]

        start = time.time()

        # =========================
        # AI PROMPT
        # =========================
        prompt = f"""
You are a healthcare classifier.

Classify the following patient symptom into ONE category only:

Categories:
- Cardiac
- Respiratory
- Neurological
- Infection
- General

Text:
{text}

Return ONLY one word category.
"""

        # =========================
        # AI CALL
        # =========================
        ai_response = client.generate(prompt)

        category = ai_response.strip().split("\n")[0]

        end = time.time()

        return jsonify({
            "category": category,
            "meta": {
                "response_time_ms": int((end - start) * 1000),
                "model_used": getattr(client, "model", "unknown")
            }
        }), 200

    except Exception as e:
        print("❌ Categorise error:", e)

        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500