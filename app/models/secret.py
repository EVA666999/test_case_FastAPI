from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from database.db import Base


class Secret(Base):
    __tablename__ = "secrets"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, comment="Уникальный идентификатор секрета"
    )
    secret: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Конфиденциальные данные, хранимые в секрете"
    )
    passphrase: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Опциональная фраза-пароль для дополнительной защиты",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Время создания секрета",
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Абсолютное время истечения срока действия секрета",
    )
    ttl_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Время жизни секрета в секундах от момента создания",
    )
    secret_key: Mapped[str] = mapped_column(
        String(360),
        unique=True,
        index=True,
        comment="Уникальный ключ доступа к секрету",
    )

    def __str__(self):
        return str(self.secret_key)

    def __repr__(self):
        return f"Secret(id={self.id}, secret_key={self.secret_key}, created_at={self.created_at}, expires_at={self.expires_at})"
