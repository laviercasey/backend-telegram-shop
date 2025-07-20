from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import create_access_token, verify_telegram_auth
from app.core.config import settings
from backend.app.crud.user import user as user_crud
from app.schemas.auth import TelegramAuth, Token, AuthResponse
from app.schemas.user import UserCreate, User

router = APIRouter()

@router.post("/telegram-login", response_model=AuthResponse)
def login_with_telegram(
    auth_data: TelegramAuth, db: Session = Depends(get_db)
) -> Any:
    auth_data_dict = auth_data.model_dump()
    
    if not verify_telegram_auth(auth_data_dict):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication data",
        )
    
    user = user_crud.get_by_telegram_id(db, telegram_id=str(auth_data.id))
    if not user:
        user_in = UserCreate(
            telegram_id=str(auth_data.id),
            username=auth_data.username,
            first_name=auth_data.first_name,
            last_name=auth_data.last_name,
        )
        user = user_crud.create(db=db, obj_in=user_in)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.telegram_id, expires_delta=access_token_expires
    )
    
    return {
        "token": {
            "access_token": access_token,
            "token_type": "bearer",
        },
        "user": user
    }

@router.post("/token", response_model=Token)
def get_access_token(
    telegram_id: str, db: Session = Depends(get_db)
) -> Any:
    user = user_crud.get_by_telegram_id(db, telegram_id=telegram_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid telegram ID",
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.telegram_id, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }
