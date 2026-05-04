from flask import Blueprint, request, jsonify
import json, re, time

analyse_bp = Blueprint("analyse", __name__)

def safe_parse(text):
    try:
        return json.loads(text)
    except:
        match = re.search(r"\{[\s\S]*?\}", text)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
    return None


@analyse_bp.route("/analyse", methods=["POST"])
def analyse():
    """
    Health Analysis API
    ---
    tags:
      - Health Analyse

    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            text:
              type: string
              example: Patient has fever and oxygen level 88%

    responses:
      200:
        description: Success
        schema:
          type: object
          properties:
            data:
              type: object
            meta:
              type: object

      400:
        description: Bad request

      500:
        description: Server error
    """

    try:
        data = request.get_json()

        if not data or "text" not in data:
            return jsonify({"error": "text required"}), 400

        text = data["text"]

        # 🔥 Fake AI response (safe for testing)
        response = """
        {
          "summary": "Patient shows mild symptoms",
          "health_risks": ["Low oxygen"],
          "key_findings": ["Oxygen below normal"]
        }
        """

        parsed = safe_parse(response)

        return jsonify({
            "data": parsed,
            "meta": {
                "response_time_ms": 120
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500