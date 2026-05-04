import os


class ChromaClient:
    def __init__(self):
        self.data = []
        print("✅ Simple DB initialized (no Chroma)")

    def load_if_empty(self):
        if self.data:
            return

        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(base_dir, "..", "data", "health_data.txt")

            with open(file_path, "r") as f:
                lines = f.readlines()

            self.data = [line.strip() for line in lines if line.strip()]

            print(f"✅ Loaded {len(self.data)} records")

        except Exception as e:
            print("❌ Load error:", e)

    def query(self, query_text):
        self.load_if_empty()

        query_text = query_text.lower()

        # 🔍 simple keyword match
        results = [
            line for line in self.data
            if query_text in line.lower()
        ]

        return results[:3]  # top 3


# global instance
chroma = ChromaClient()