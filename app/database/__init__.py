import asyncio
import os
from sqlalchemy import create_engine, insert, select, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from dotenv import load_dotenv

load_dotenv()

POSTGRES_USER = os.getenv("POSTGRES_USER_local")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD_local")
POSTGRES_DB = os.getenv("POSTGRES_DB_local")
DB_HOST = os.getenv("DB_HOST_local")
DB_PORT = os.getenv("DB_PORT_local")

DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DB_HOST}:{DB_PORT}/{POSTGRES_DB}"

engine = create_async_engine(DATABASE_URL, echo=True)


async_session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

class Base(DeclarativeBase):
    pass
