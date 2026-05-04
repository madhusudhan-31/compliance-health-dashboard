from flask import Blueprint, request, jsonify
from services.chroma_client import chroma
from services.groq_client import groq_client

query_bp = Blueprint("query", __name__)


@query_bp.route("/query", methods=["POST"])
def query():
    """
    Health Query with AI
    ---
    tags:
      - Query
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            query:
              type: string
              example: fever
    responses:
      200:
        description: Success
    """

    data = request.get_json()

    if not data or "query" not in data:
        return jsonify({"error": "Query required"}), 400

    user_query = data["query"]

    results = chroma.query(user_query)

    ai_response = groq_client.generate(user_query, results)

    return jsonify({
        "query": user_query,
        "results": results,
        "ai_response": ai_response
    })