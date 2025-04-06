from datetime import datetime, timedelta, timezone
import uuid
from fastapi import APIRouter, Depends, status, HTTPException, Request
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
from models.log import SecretLog
from schemas import CreateSecret
from services.encryption_service import EncryptionService

router = APIRouter(prefix='/secrets', tags=['secrets'])


@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_secret(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    create_secret: CreateSecret,
    _: Annotated[None, Depends(no_cache_headers)]
):  
    
    secret_key = str(uuid.uuid4())
    encrypted_secret = EncryptionService.encrypt(create_secret.secret)
    
    encrypted_passphrase = None
    if create_secret.passphrase:
        encrypted_passphrase = EncryptionService.encrypt(create_secret.passphrase)

    insert_data = {
        "secret": encrypted_secret,
        "passphrase": encrypted_passphrase,
        "ttl_seconds": create_secret.ttl_seconds,
    }
    
    if create_secret.ttl_seconds is not None:
        insert_data["expires_at"] = datetime.now(timezone.utc) + timedelta(seconds=create_secret.ttl_seconds)
    
    result = await db.execute(
        insert(Secret).values(**insert_data).returning(Secret)
    )
    secret_key_uuid = await db.execute(insert(Secret).values(secret_key).returning(Secret))
    secret = result.scalar_one()

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent", "Unknown")
    
    log_data = {
        "secret_id": secret.id,
        "action": "create",
        "ip_address": client_ip,
        "user_agent": user_agent,
        "ttl_seconds": create_secret.ttl_seconds
    }
    await db.execute(insert(SecretLog).values(**log_data))
    await db.commit()

    #кэша
    secret_data = {
        "id": secret.id,
        "secret": encrypted_secret,
        "passphrase": encrypted_passphrase,
        "created_at": secret.created_at.isoformat(),
        "expires_at": secret.expires_at.isoformat() if secret.expires_at else None,
        "ttl_seconds": secret.ttl_seconds,

    }
    
    await RedisService.cache_secret(str(secret.id), secret_data, secret.ttl_seconds)

    return {
        "secret_key": secret_key
    }

@router.get('/{secret_key}', status_code=status.HTTP_200_OK)
async def get_secret(
                request: Request,
                _: Annotated[None, Depends(no_cache_headers)],
                db: Annotated[AsyncSession, Depends(get_db)], 
                secret_id: int
            ):
    secret = await db.scalar(select(Secret).where(Secret.id == secret_id))
    if secret is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There is no secret found'
        )
    
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent", "Unknown")
    
    log_data = {
        "secret_id": secret.id,
        "action": "read",
        "ip_address": client_ip,
        "user_agent": user_agent,
        "ttl_seconds": secret.ttl_seconds,
        "timestamp": datetime.now()
    }
    await db.execute(insert(SecretLog).values(**log_data))

    await db.delete(secret)

    await db.commit()

    return {
        "secret": secret
    }
