import asyncio
import json
import os

import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)  # Стандартный порт Redis
REDIS_DB = os.getenv("REDIS_DB", 0)

print(f"Redis config: {REDIS_HOST}:{REDIS_PORT}")

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=int(REDIS_PORT),
    db=int(REDIS_DB),
    decode_responses=True,
    socket_timeout=10.0,  # Добавляем таймаут
)

MIN_CACHE_TTL = 300


class RedisService:
    """Простой сервис для работы с Redis"""

    @staticmethod
    async def cache_secret(secret_id: str, data: dict, ttl_seconds: int = None):
        """Кеширует секрет в Redis"""
        json_data = json.dumps(data)
        actual_ttl = max(MIN_CACHE_TTL, ttl_seconds or MIN_CACHE_TTL)

        try:
            await redis_client.set(f"secret:{secret_id}", json_data, ex=actual_ttl)
            print(f"Secret {secret_id} cached successfully")
        except Exception as e:
            print(f"Error caching secret: {e}")

    @staticmethod
    async def get_cached_secret(secret_id: str) -> dict:
        """Получает секрет из Redis"""
        try:
            data = await redis_client.get(f"secret:{secret_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Error getting cached secret: {e}")
            return None

    @staticmethod
    async def delete_cached_secret(secret_id: str):
        """Удаляет секрет из Redis"""
        try:
            await redis_client.delete(f"secret:{secret_id}")
            print(f"Secret {secret_id} deleted from cache")
        except Exception as e:
            print(f"Error deleting cached secret: {e}")

    @staticmethod
    async def ping():
        """Проверяет соединение с Redis"""
        try:
            for i in range(5):  # Попробуем 5 раз с интервалом
                try:
                    result = await redis_client.ping()
                    print(f"Redis ping successful: {result}")
                    return result
                except Exception as e:
                    print(f"Redis ping attempt {i+1} failed: {e}")
                    if i < 4:  # Не ждем после последней попытки
                        await asyncio.sleep(2)
            print("All Redis ping attempts failed")
            return False
        except Exception as e:
            print(f"Error pinging Redis: {e}")
            return False

    @staticmethod
    async def close():
        """Закрывает соединение с Redis"""
        try:
            await redis_client.close()
            print("Redis connection closed")
        except Exception as e:
            print(f"Error closing Redis connection: {e}")
