FROM python:3.11-slim

WORKDIR /app

# Установка необходимых зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    postgresql-client \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements первым слоем для кэширования 
COPY ./requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Копируем все остальное
COPY ./app .

# Создаем скрипт ожидания
RUN echo '#!/bin/bash\n\
while ! pg_isready -h $DB_HOST -p $DB_PORT -U $POSTGRES_USER 2>/dev/null; do\n\
    echo "Waiting for PostgreSQL to be ready..."\n\
    sleep 2\n\
done\n\
while ! redis-cli -h $REDIS_HOST -p $REDIS_PORT ping 2>/dev/null; do\n\
    echo "Waiting for Redis to be ready..."\n\
    sleep 2\n\
done\n\
exec "$@"' > /wait-for-services.sh \
    && chmod +x /wait-for-services.sh

ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POSTGRES_HOST=postgres \
    REDIS_HOST=redis

EXPOSE 8000

# Используем созданный скрипт как точку входа
ENTRYPOINT ["/wait-for-services.sh"]

# Команда по умолчанию
CMD alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000 --reload