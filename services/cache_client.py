import redis
import os


class CacheClient:
    def __init__(self):
        try:
            redis_url = os.getenv("REDIS_URL")

            if redis_url:
                self.client = redis.from_url(redis_url, decode_responses=True)
                print("✅ Connected to Redis (Render)")
            else:
                self.client = redis.Redis(
                    host="localhost",
                    port=6379,
                    db=0,
                    decode_responses=True
                )
                print("✅ Connected to Redis (Local)")

        except Exception:
            print("❌ Redis not available, using memory cache")
            self.client = None
            self.memory_cache = {}

    def get(self, key):
        try:
            if self.client:
                return self.client.get(key)
            return self.memory_cache.get(key)
        except:
            return None

    def setex(self, key, ttl, value):
        try:
            if self.client:
                self.client.setex(key, ttl, value)
            else:
                self.memory_cache[key] = value
        except:
            pass


cache_client = CacheClient()