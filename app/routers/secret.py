import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.database import get_db
from dependencies.security import no_cache_headers
from models.log import SecretLog
from models.secret import Secret
from schemas import CreateSecret
from services.encryption_service import EncryptionService
from services.redis_service import RedisService

router = APIRouter(prefix="/secrets", tags=["secrets"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_secret(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    create_secret: CreateSecret,
    _: Annotated[None, Depends(no_cache_headers)],
):

    secret_key = str(uuid.uuid4())
    encrypted_secret = EncryptionService.encrypt(create_secret.secret)
    encrypted_passphrase = EncryptionService.encrypt(create_secret.passphrase)

    insert_data = {
        "secret": encrypted_secret,
        "passphrase": encrypted_passphrase,
        "ttl_seconds": create_secret.ttl_seconds,
        "secret_key": secret_key,
    }

    if create_secret.ttl_seconds is not None:
        insert_data["expires_at"] = datetime.now(timezone.utc) + timedelta(
            seconds=create_secret.ttl_seconds
        )

    result = await db.execute(insert(Secret).values(**insert_data).returning(Secret))
    secret = result.scalar_one()

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent", "Unknown")

    log_data = {
        "secret_id": secret.id,
        "action": "create",
        "ip_address": client_ip,
        "user_agent": user_agent,
        "ttl_seconds": create_secret.ttl_seconds,
    }
    await db.execute(insert(SecretLog).values(**log_data))
    await db.commit()

    # кэша
    secret_data = {
        "id": secret.id,
        "secret": encrypted_secret,
        "passphrase": encrypted_passphrase,
        "created_at": secret.created_at.isoformat(),
        "expires_at": secret.expires_at.isoformat() if secret.expires_at else None,
        "ttl_seconds": secret.ttl_seconds,
    }

    await RedisService.cache_secret(str(secret.id), secret_data, secret.ttl_seconds)

    return {"secret_key": secret_key}


@router.get("/{secret_key}", status_code=status.HTTP_200_OK)
async def get_secret(
    request: Request,
    _: Annotated[None, Depends(no_cache_headers)],
    db: Annotated[AsyncSession, Depends(get_db)],
    secret_key: str,
):
    secret = await db.scalar(select(Secret).where(Secret.secret_key == secret_key))

    if secret is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Secret not found"
        )

    now = datetime.now(timezone.utc)

    if secret.expires_at < now:
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("User-Agent", "Unknown")
        log_data = {
            "secret_id": secret.id,
            "action": "expired_access",
            "ip_address": client_ip,
            "user_agent": user_agent,
            "additional_info": "Attempt to access expired secret",
        }
        await db.execute(insert(SecretLog).values(**log_data))
        await db.delete(secret)
        await RedisService.delete_cached_secret(str(secret.id))
        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Secret has expired"
        )

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent", "Unknown")
    log_data = {
        "secret_id": secret.id,
        "action": "delete",
        "ip_address": client_ip,
        "user_agent": user_agent,
        "ttl_seconds": secret.ttl_seconds,
        "timestamp": datetime.now(),
    }
    await db.execute(insert(SecretLog).values(**log_data))

    decrypted_secret = EncryptionService.decrypt(secret.secret)

    await db.delete(secret)
    await RedisService.delete_cached_secret(str(secret.id))
    await db.commit()

    return {"secret": decrypted_secret}


@router.delete("/{secret_key}", status_code=status.HTTP_200_OK)
async def delete_secret(
    request: Request,
    _: Annotated[None, Depends(no_cache_headers)],
    db: Annotated[AsyncSession, Depends(get_db)],
    secret_key: str,
    passphrase: str = None,
):
    secret = await db.scalar(select(Secret).where(Secret.secret_key == secret_key))

    if secret is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Secret not found"
        )

    if secret.passphrase:
        decrypted_passphrase = EncryptionService.decrypt(secret.passphrase)
        if passphrase != decrypted_passphrase:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Incorrect passphrase"
            )

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent", "Unknown")
    log_data = {
        "secret_id": secret.id,
        "action": "delete",
        "ip_address": client_ip,
        "user_agent": user_agent,
        "additional_info": "Deleted by user request",
    }
    await db.execute(insert(SecretLog).values(**log_data))

    await RedisService.delete_cached_secret(str(secret.id))

    await db.delete(secret)
    await db.commit()

    return {"status": "secret_deleted"}
