from celery import Celery
from datetime import datetime, timezone
from sqlalchemy import select
from models.secret import Secret
from models.log import SecretLog
from database.db import async_session_maker

celery = Celery("secrets_app", broker="redis://localhost:6379/0")

@celery.task
def cleanup_expired_secrets():
    """Удаляет просроченные секреты"""
    with async_session_maker() as db:
        now = datetime.now(timezone.utc)
        
        expired_secrets = db.execute(
            select(Secret).where(Secret.expires_at < now)
        ).scalars().all()
        for secret in expired_secrets:
            db.add(SecretLog(
                secret_id=secret.id,
                action="auto_delete",
                additional_info="TTL expired"
            ))
            db.delete(secret)
        db.commit()
    
    return f"Удалено {len(expired_secrets)} просроченных секретов"