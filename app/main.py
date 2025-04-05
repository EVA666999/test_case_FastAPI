from routers import secret
from fastapi import FastAPI

app = FastAPI()

app.include_router(secret.router)