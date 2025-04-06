from pydantic import BaseModel, Field
from datetime import date, datetime

class CreateSecret(BaseModel):
    secret: str
    passphrase: str | None = Field(default=None, min_length=8, description="Passphrase must be at least 8 characters long")
    ttl_seconds: int | None = Field(default=None, gt=0, description="Time to live in seconds, must be greater than 0")