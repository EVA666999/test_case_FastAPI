"""Логирование модели Secret"""

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Text, String, DateTime, Integer, ForeignKey
from sqlalchemy.sql import func
from datetime import datetime
from database.db import Base

class SecretLog(Base):
    __tablename__ = "secret_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, 
                                   comment="Уникальный идентификатор записи лога")
    secret_id: Mapped[int] = mapped_column(Integer, nullable=False, 
                                         comment="ID созданного секрета")
    action: Mapped[str] = mapped_column(String(50), nullable=False, 
                                      comment="Тип действия (создание, чтение, удаление)")
    ip_address: Mapped[str] = mapped_column(String(50), nullable=True, 
                                         comment="IP-адрес клиента")
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True, 
                                                comment="User-Agent клиента")
    ttl_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True, 
                                                 comment="Время жизни секрета в секундах")
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), 
                                             comment="Время выполнения действия")
    additional_info: Mapped[str | None] = mapped_column(Text, nullable=True, 
                                                     comment="Дополнительная информация")
    
    def __repr__(self):
        return f"SecretLog(id={self.id}, secret_id={self.secret_id}, action={self.action}, timestamp={self.timestamp})"