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
            log_entry = SecretLog(
                secret_id=secret.id,
                action="auto_delete",
                ip_address=None,
                user_agent=None,
                ttl_seconds=secret.ttl_seconds,
                timestamp=now,
                additional_info="Secret expired and automatically deleted"
            )
            db.add(log_entry)
            
            db.delete(secret)
        
        db.commit()
    
    return f"Удалено {len(expired_secrets)} просроченных секретов"