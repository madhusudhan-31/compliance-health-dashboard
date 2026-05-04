import os
from services.chroma_client import ChromaClient


def load_data_to_chroma():
    print("📦 Starting ChromaDB loader...")

    chroma = ChromaClient()

    if not chroma.collection:
        raise Exception("Chroma collection not initialized")

    # ❌ REMOVE count() check completely

    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "..", "data", "health_data.txt")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"❌ File not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        texts = [line.strip() for line in f if line.strip()]

    print(f"📥 Loading {len(texts)} records...")

    # ✅ Try insert directly (Chroma will handle duplicates if any)
    chroma.add_data(texts)

    print("✅ Data loaded successfully")