from pydantic import BaseModel
from datetime import date, datetime

class CreateSecret(BaseModel):
    secret: str
    passphrase: str | None = None
    ttl_seconds: int | None = None