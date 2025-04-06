from celery import Celery
from datetime import datetime, timezone
from sqlalchemy import select, and_, func
from models.secret import Secret
from models.log import SecretLog
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import logging
import redis

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загружаем .env файл
load_dotenv()

# Подготавливаем параметры подключения к БД
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)
REDIS_DB = os.getenv("REDIS_DB")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DB_HOST}:{DB_PORT}/{POSTGRES_DB}"


redis_client = redis.Redis(
    host=REDIS_HOST, 
    port=int(REDIS_PORT), 
    db=int(REDIS_DB)
)


# Инициализируем Celery
celery = Celery("secrets_app", 
                broker=f"redis://{REDIS_HOST}:{REDIS_PORT}/0", 
                backend=f"redis://{REDIS_HOST}:{REDIS_PORT}/0")

# Конфигурация Celery
celery.conf.beat_schedule = {
    'cleanup-expired-secrets': {
        'task': 'cleanup_expired_secrets',
        'schedule': 60.0,
    },
}
celery.conf.timezone = 'UTC'

@celery.task(name='cleanup_expired_secrets')
def cleanup_expired_secrets():
    logger.info("Начинаем проверку просроченных секретов")
    
    try:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(engine)
        
        with SessionLocal() as db:
            now = datetime.now(timezone.utc)
            logger.info(f"Текущее время UTC: {now}")
            
            # Получаем просроченные секреты с явным приведением времени
            expired_secrets = db.execute(
                select(Secret).where(
                    and_(
                        Secret.expires_at != None, 
                        Secret.expires_at <= now  # Используем прямое сравнение с now
                    )
                )
            ).scalars().all()
            
            logger.info(f"Найдено просроченных секретов: {len(expired_secrets)}")
            
            for secret in expired_secrets:
                redis_client.delete(f"secret:{secret.id}")

                logger.info(f"Удаляем просроченный секрет:")
                logger.info(f"  ID: {secret.id}")
                logger.info(f"  Создан: {secret.created_at}")
                logger.info(f"  Истекает: {secret.expires_at}")
                logger.info(f"  Текущее время: {now}")
                
                log_entry = SecretLog(
                    secret_id=secret.id,
                    action="auto_delete",
                    ip_address="system",
                    user_agent="Celery Task",
                    ttl_seconds=secret.ttl_seconds,
                    timestamp=now,
                    additional_info=f"Secret expired. Created: {secret.created_at}, Expires: {secret.expires_at}"
                )
                db.add(log_entry)
                db.delete(secret)
            
            db.commit()
            logger.info(f"Удалено {len(expired_secrets)} просроченных секретов")
        
        return f"Удалено {len(expired_secrets)} просроченных секретов"
    except Exception as e:
        logger.error(f"Ошибка при очистке просроченных секретов: {e}", exc_info=True)
        raise