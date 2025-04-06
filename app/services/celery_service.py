from celery import Celery
from datetime import datetime, timezone
from sqlalchemy import select, and_
from models.secret import Secret
from models.log import SecretLog
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import redis

load_dotenv()

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DB_HOST}:{DB_PORT}/{POSTGRES_DB}"

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"), 
    port=int(os.getenv("REDIS_PORT", 6379)), 
    db=int(os.getenv("REDIS_DB", 0))
)

celery = Celery("secrets_app", broker="redis://localhost:6379/0")

@celery.task(name='cleanup_expired_secrets')
def cleanup_expired_secrets():
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(engine)
    
    with SessionLocal() as db:
        now = datetime.now(timezone.utc)
        
        expired_secrets = db.execute(
            select(Secret).where(
                and_(
                    Secret.expires_at != None, 
                    Secret.expires_at <= now
                )
            )
        ).scalars().all()
        
        for secret in expired_secrets:
            redis_client.delete(f"secret:{secret.id}")
            
            log_entry = SecretLog(
                secret_id=secret.id,
                action="auto_delete",
                ip_address="system",
                user_agent="Celery Task",
                ttl_seconds=secret.ttl_seconds,
                timestamp=now
            )
            db.add(log_entry)
            db.delete(secret)
        
        db.commit()
        
        return f"Удалено {len(expired_secrets)} просроченных секретов"