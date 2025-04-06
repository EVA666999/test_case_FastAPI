from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from sqlalchemy import delete, insert, select, update
from slugify import slugify
import uvicorn
from sqlalchemy.ext.asyncio import AsyncSession
from services.redis_service import RedisService
from dependencies.database import get_db
from dependencies.security import no_cache_headers
from models.secret import Secret
from schemas import CreateSecret
from services.encryption_service import EncryptionService

router = APIRouter(prefix='/secrets', tags=['secrets'])


@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_secret(
    db: Annotated[AsyncSession, Depends(get_db)],
    create_secret: CreateSecret,
    _: Annotated[None, Depends(no_cache_headers)]
):  
    encrypted_secret = EncryptionService.encrypt(create_secret.secret)

    insert_data = {
        "secret": create_secret.secret,
        "passphrase": create_secret.passphrase,
        "ttl_seconds": create_secret.ttl_seconds,
    }
    
    if create_secret.ttl_seconds is not None:
        insert_data["expires_at"] = datetime.now(timezone.utc) + timedelta(seconds=create_secret.ttl_seconds)
    
    result = await db.execute(
        insert(Secret).values(**insert_data).returning(Secret.id)
    )
    secret_id = result.scalar_one()
    
    await db.commit()

    result = await db.execute(select(Secret).where(Secret.id == secret_id))
    secret = result.scalar_one()

    secret_data = {
        "id": secret.id,
        "secret": encrypted_secret,
        "passphrase": encrypted_secret,
        "created_at": secret.created_at.isoformat(),
        "expires_at": secret.expires_at.isoformat() if secret.expires_at else None,
        "ttl_seconds": secret.ttl_seconds,
    }
    
    await RedisService.cache_secret(str(secret.id), secret_data, secret.ttl_seconds)

    return {
        "secret_key": str(secret)
    }