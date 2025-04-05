from pydantic import BaseModel
from datetime import date, datetime

class CreateSecret(BaseModel):
    secret: str
    passphrase: str | None = None  # Опционально, как в ТЗ
    ttl_seconds: int | None = None  # Опционально, как в ТЗ