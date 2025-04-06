from contextlib import asynccontextmanager
from fastapi import FastAPI
from routers import secret
from services.redis_service import RedisService
from services import celery_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Запуск приложения...")
    await RedisService.ping()
    yield
    print("Остановка приложения...")
    await RedisService.close()

app = FastAPI(
    title="Secret Storage API",
    description="API для безопасного хранения секретов",
    version="1.0.0",
    lifespan=lifespan
)

celery_service.celery.conf.beat_schedule = {
    'cleanup-expired-secrets': {
        'task': 'cleanup_expired_secrets',
        'schedule': 3600.0,
    },
}

app.include_router(secret.router)

