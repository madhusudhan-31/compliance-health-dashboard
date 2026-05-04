from flask import Blueprint, jsonify
import time
from datetime import datetime

from services.metrics import start_time
from services.shared import groq_client as groq
from services.shared import cache_client as cache
from services.shared import chroma_client as chroma

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health():

    # ✅ FORCE MODEL LOAD (VERY IMPORTANT)
    try:
        groq._pick_working_model()
    except:
        pass

    uptime = int(time.time() - start_time)

    # Model
    model_name = getattr(groq, "model", "unknown")

    # Avg response time
    try:
        avg_time = round(groq.get_avg_response_time(), 2)
    except:
        avg_time = 0

    # Chroma count
    try:
        if hasattr(chroma, "count"):
            doc_count = chroma.count()
        else:
            doc_count = chroma.collection.count()
    except:
        doc_count = 0

    # Cache stats
    try:
        cache_stats = cache.get_stats()
    except:
        cache_stats = {"hits": 0, "miss": 0}

    return jsonify({
        "status": "healthy",
        "model": model_name,
        "avg_response_time_ms": avg_time,
        "chroma_doc_count": doc_count,
        "uptime_seconds": uptime,
        "cache": cache_stats,
        "timestamp": datetime.utcnow().isoformat()
    })