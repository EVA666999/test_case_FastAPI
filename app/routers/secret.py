from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from sqlalchemy import delete, insert, select, update
from slugify import slugify
import uvicorn
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies.database import get_db
from dependencies.security import no_cache_headers
from models.secret import Secret
from schemas import CreateSecret

router = APIRouter(prefix='/secrets', tags=['secrets'])


@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_secret(
    db: Annotated[AsyncSession, Depends(get_db)],
    create_secret: CreateSecret,
    _: Annotated[None, Depends(no_cache_headers)]
):
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
    
    return {
        "secret_key": str(secret_id)
    }