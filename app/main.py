from contextlib import asynccontextmanager
from fastapi import FastAPI
from routers import secret
from services.redis_service import RedisService

# Обработчик жизненного цикла приложения
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

app.include_router(secret.router)

