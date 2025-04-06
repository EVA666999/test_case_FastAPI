from celery import Celery
from datetime import datetime, timezone
from sqlalchemy import select, and_
from models.secret import Secret
from models.log import SecretLog
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
from sqlalchemy import select, and_, func
from datetime import datetime, timezone
import logging

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

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DB_HOST}:{DB_PORT}/{POSTGRES_DB}"

# Инициализируем Celery
celery = Celery("secrets_app", broker="redis://localhost:6379/0")

@celery.task(name='cleanup_expired_secrets')
def cleanup_expired_secrets():
    logger.info("Начинаем проверку просроченных секретов")
    
    try:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(engine)
        
        with SessionLocal() as db:
            now = datetime.now(timezone.utc)
            logger.info(f"Текущее время UTC: {now}")
            
            # Получаем просроченные секреты
            expired_secrets = db.execute(
                select(Secret).where(
                    and_(
                        Secret.expires_at != None, 
                        Secret.expires_at < func.now()
                    )
                )
            ).scalars().all()
            
            logger.info(f"Найдено просроченных секретов: {len(expired_secrets)}")
            
            for secret in expired_secrets:
                logger.info(f"Удаляем просроченный секрет с ID {secret.id}, expire_at={secret.expires_at}")
                
                log_entry = SecretLog(
                    secret_id=secret.id,
                    action="auto_delete",
                    ip_address="system",
                    user_agent="Celery Task",
                    ttl_seconds=secret.ttl_seconds,
                    timestamp=now,
                    additional_info="Secret expired and automatically deleted"
                )
                db.add(log_entry)
                db.delete(secret)
            
            db.commit()
            logger.info(f"Удалено {len(expired_secrets)} просроченных секретов")
        
        return f"Удалено {len(expired_secrets)} просроченных секретов"
    except Exception as e:
        logger.error(f"Ошибка при очистке просроченных секретов: {e}", exc_info=True)
        raise