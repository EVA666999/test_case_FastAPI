import os
import json
import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", 6380)
REDIS_DB = os.getenv("REDIS_DB", 0)

redis_client = redis.Redis(host=REDIS_HOST, port=int(REDIS_PORT), db=int(REDIS_DB), decode_responses=True)

MIN_CACHE_TTL = 300

class RedisService:
    """Простой сервис для работы с Redis"""
    
    @staticmethod
    async def cache_secret(secret_id: str, data: dict, ttl_seconds: int = None):
        """Кеширует секрет в Redis"""
        json_data = json.dumps(data)
        actual_ttl = max(MIN_CACHE_TTL, ttl_seconds or MIN_CACHE_TTL)
        
        await redis_client.set(f"secret:{secret_id}", json_data, ex=actual_ttl)
    
    @staticmethod
    async def get_cached_secret(secret_id: str) -> dict:
        """Получает секрет из Redis"""
        data = await redis_client.get(f"secret:{secret_id}")
        
        if data:
            return json.loads(data)
        return None
    
    @staticmethod
    async def delete_cached_secret(secret_id: str):
        """Удаляет секрет из Redis"""
        await redis_client.delete(f"secret:{secret_id}")
    
    @staticmethod
    async def ping():
        """Проверяет соединение с Redis"""
        return await redis_client.ping()
    
    @staticmethod
    async def close():
        """Закрывает соединение с Redis"""
        await redis_client.close()