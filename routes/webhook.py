from flask import Blueprint, request, jsonify
import json
from datetime import datetime

webhook_bp = Blueprint("webhook", __name__)


@webhook_bp.route("/webhook", methods=["POST"])
def webhook():
    """
    Webhook receiver for async health report results
    ---
    tags:
      - Health Webhook

    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            job_id:
              type: string
              example: abc123
            status:
              type: string
              example: completed
            result:
              type: object
              properties:
                title:
                  type: string
                summary:
                  type: string
                risk_level:
                  type: string
                key_findings:
                  type: array
                  items:
                    type: string
                recommendations:
                  type: array
                  items:
                    type: string

    responses:
      200:
        description: Webhook received
    """

    try:
        # ✅ Safe JSON handling (prevents 415)
        data = request.get_json(silent=True)

        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        job_id = data.get("job_id")
        status = data.get("status")
        result = data.get("result")

        # ✅ Validation
        if not job_id or not status:
            return jsonify({
                "error": "Missing required fields",
                "required": ["job_id", "status"]
            }), 400

        # =========================
        # LOGGING (clean format)
        # =========================
        print("\n🔥 WEBHOOK RECEIVED")
        print("Time:", datetime.utcnow().isoformat())
        print("Job ID:", job_id)
        print("Status:", status)

        if result:
            print("Result:", json.dumps(result, indent=2))

        # =========================
        # OPTIONAL: Save to DB / file
        # =========================
        # with open("webhook_logs.json", "a") as f:
        #     f.write(json.dumps(data) + "\n")

        return jsonify({
            "status": "received",
            "job_id": job_id
        }), 200

    except Exception as e:
        print("❌ Webhook error:", e)

        return jsonify({
            "error": "Webhook processing failed",
            "message": str(e)
        }), 500