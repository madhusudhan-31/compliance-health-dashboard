from flask import Blueprint, request, jsonify
from datetime import datetime
import json
import re
import hashlib
import time
import traceback

from services.shared import groq_client as client
from services.shared import cache_client as cache
from services.shared import chroma_client

describe_bp = Blueprint("describe", __name__)


# =========================
# Load Prompt
# =========================
def load_prompt():
    try:
        with open("prompts/describe_prompt.txt", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return """
Analyze the following patient input and return JSON:

Text:
{text}

STRICT RULES:
- Return ONLY JSON

FORMAT:
{
  "health_risk_level": "Low/Medium/High",
  "explanation": "short explanation",
  "key_indicators": ["item1", "item2"]
}
"""

PROMPT_TEMPLATE = load_prompt()


# =========================
# Cache Key
# =========================
def generate_cache_key(text):
    normalized = " ".join(text.lower().split())
    return hashlib.sha256(normalized.encode()).hexdigest()


# =========================
# Safe JSON Parser
# =========================
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


# =========================
# ROUTE
# =========================
@describe_bp.route("/describe", methods=["POST"])
def describe():
    """
    Analyze patient health risk using AI + RAG
    ---
    tags:
      - Health Describe

    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            text:
              type: string
              example: Patient has fever, cough, and oxygen level 90%

    responses:
      200:
        description: Health risk analysis result
    """

    try:
        # =========================
        # Validate input
        # =========================
        data = request.get_json(silent=True)

        if not data or "text" not in data:
            return jsonify({"error": "Missing 'text' field"}), 400

        text = data["text"]

        # =========================
        # Cache check
        # =========================
        key = generate_cache_key(text)

        try:
            cached = cache.get(key)
        except:
            cached = None

        if cached:
            if isinstance(cached, bytes):
                cached = cached.decode()

            cached_data = json.loads(cached)
            cached_data["meta"]["cached"] = True
            return jsonify(cached_data), 200

        # =========================
        # RAG Context (SAFE)
        # =========================
        try:
            docs = chroma_client.query(text)

            if docs and len(docs) > 0:
                context = "\n".join(docs[0])
            else:
                context = ""
        except:
            context = ""

        # =========================
        # Build Prompt
        # =========================
        prompt = PROMPT_TEMPLATE.replace("{text}", text)

        # =========================
        # Call AI (FIXED)
        # =========================
        start = time.time()

        response = client.generate(
            query=prompt,
            context=context   # ✅ proper usage
        )

        end = time.time()

        print("🧠 RAW RESPONSE:", response)

        # =========================
        # Parse JSON
        # =========================
        parsed = safe_parse(response)

        if not parsed:
            parsed = {
                "health_risk_level": "Unknown",
                "explanation": "Model returned unstructured output",
                "key_indicators": [response[:200]]
            }

        # =========================
        # Final Response
        # =========================
        result = {
            "data": parsed,
            "meta": {
                "model_used": getattr(client, "model", "unknown"),
                "response_time_ms": int((end - start) * 1000),
                "cached": False,
                "timestamp": datetime.utcnow().isoformat()
            }
        }

        # =========================
        # Cache Save
        # =========================
        try:
            cache.set(key, json.dumps(result))
        except:
            pass

        return jsonify(result), 200

    except Exception as e:
        print("❌ ERROR:", traceback.format_exc())

        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500