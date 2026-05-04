import os
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class GroqClient:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise Exception("❌ GROQ_API_KEY not found in .env")

        self.client = Groq(api_key=api_key)

        self.preferred_models = [
            "llama-3.1-8b-instant",
            "llama-3.1-70b-versatile",
            "gemma2-9b-it"
        ]

        self._working_model = None
        self.model = None
        self.last_response_time = 0
        self.total_response_time = 0
        self.call_count = 0

    def _pick_working_model(self):
        if self._working_model:
            return self._working_model

        try:
            models = self.client.models.list().data
            available = {m.id for m in models}
        except Exception:
            available = set()

        for m in self.preferred_models:
            if not available or m in available:
                self._working_model = m
                self.model = m   # ✅ FIX
                print(f"✅ Using model: {m}")
                return m

        raise Exception("❌ No working model found")

    def generate(self, query, context=None):
        model = self._pick_working_model()

        if not context:
            context = "General health data"

        prompt = f"""
You are a healthcare assistant.

User Question:
{query}

Relevant Data:
{context}

Give:
- Short explanation
- Possible cause
- Basic advice
"""

        try:
            start = time.time()

            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4
            )

            end = time.time()

            t = int((end - start) * 1000)
            self.last_response_time = t
            self.total_response_time += t
            self.call_count += 1

            return response.choices[0].message.content

        except Exception as e:
            print("❌ Groq error:", e)
            return "AI response unavailable"

    def get_avg_response_time(self):
        if self.call_count == 0:
            return 0
        return self.total_response_time / self.call_count


# ✅ global instance
groq_client = GroqClient()