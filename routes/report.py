from flask import Blueprint, request, jsonify
from services.job_service import create_job, update_job, get_job, run_async
from services.shared import groq_client as groq
import requests
import json
import re

report_bp = Blueprint("report", __name__)


# =========================
# SAFE JSON EXTRACTOR
# =========================
def extract_json(response):
    try:
        response = re.sub(r"```json|```", "", response).strip()
        match = re.search(r"\{[\s\S]*\}", response)
        if match:
            return json.loads(match.group())
    except:
        pass
    return None


# =========================
# CORE AI LOGIC (HEALTH)
# =========================
def generate_report_logic(text):
    prompt = f"""
You are a healthcare AI system.

Analyze the patient data and generate a structured health report.

STRICT RULES:
- Return ONLY JSON
- No markdown
- No explanation outside JSON

FORMAT:
{{
  "title": "Health Report",
  "summary": "short summary",
  "risk_level": "Low/Medium/High",
  "key_findings": ["finding1", "finding2"],
  "recommendations": ["rec1", "rec2"]
}}

Patient Data:
{text}
"""

    try:
        response = groq.generate(prompt)
        print("🧠 RAW RESPONSE:", response)

        parsed = extract_json(response)
        if parsed:
            return parsed

    except Exception as e:
        print("❌ AI ERROR:", e)

    # fallback
    return {
        "title": "Health Report",
        "summary": "Unable to generate structured report",
        "risk_level": "Unknown",
        "key_findings": [text],
        "recommendations": ["Consult doctor"]
    }


# =========================
# BACKGROUND JOB
# =========================
def process_job(job_id, text, webhook_url=None):
    try:
        result = generate_report_logic(text)

        update_job(job_id, {
            "status": "completed",
            "result": result
        })

        # ✅ FIXED webhook validation
        if webhook_url and webhook_url.startswith("http"):
            try:
                requests.post(
                    webhook_url,
                    json={
                        "job_id": job_id,
                        "status": "completed",
                        "result": result
                    },
                    timeout=5
                )
            except Exception as e:
                print("⚠️ Webhook failed:", e)
        else:
            print("⚠️ Invalid webhook URL, skipped")

    except Exception as e:
        update_job(job_id, {
            "status": "failed",
            "error": str(e)
        })


# =========================
# CREATE JOB
# =========================
@report_bp.route("/generate-report", methods=["POST"])
def generate_report():
    """
    Generate health report asynchronously
    ---
    tags:
      - Health Report

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
            webhook_url:
              type: string
              example: https://webhook.site/your-id

    responses:
      200:
        description: Job created
    """

    # ✅ FIXED JSON handling (no 415 error)
    data = request.get_json(silent=True)

    if not data or "text" not in data:
        return jsonify({
            "error": "text field is required",
            "example": {
                "text": "Patient has fever and low oxygen"
            }
        }), 400

    text = data["text"]
    webhook_url = data.get("webhook_url")

    # ✅ create job
    job_id = create_job()

    # ✅ run async
    run_async(process_job, (job_id, text, webhook_url))

    return jsonify({
        "job_id": job_id,
        "status": "processing"
    })


# =========================
# JOB STATUS
# =========================
@report_bp.route("/job-status/<job_id>", methods=["GET"])
def job_status(job_id):
    """
    Get report job status
    ---
    tags:
      - Health Report

    parameters:
      - name: job_id
        in: path
        type: string
        required: true
        description: Job ID returned from /generate-report
        example: abc123

    responses:
      200:
        description: Job status
      404:
        description: Invalid job_id
    """

    job = get_job(job_id)

    if not job:
        return jsonify({
            "error": "Invalid job_id",
            "hint": "Use job_id from /generate-report"
        }), 404

    return jsonify(job)