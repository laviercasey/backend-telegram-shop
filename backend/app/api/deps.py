from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user, check_user_role
from app.models.user import User
from backend.app.crud.shop import shop as shop_crud

def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_shop_owner(
    shop_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> User:
    shop = shop_crud.get(db=db, id=shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    if shop.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user

def get_shop_admin(
    shop_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> User:
    shop = shop_crud.get(db=db, id=shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    if shop.owner_id == current_user.id:
        return current_user
    
    if check_user_role(current_user, "admin", shop_id, db):
        return current_user
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not enough permissions",
    )

def get_shop_manager(
    shop_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> User:
    shop = shop_crud.get(db=db, id=shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    if shop.owner_id == current_user.id:
        return current_user
    
    if check_user_role(current_user, "admin", shop_id, db) or check_user_role(current_user, "manager", shop_id, db):
        return current_user
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not enough permissions",
    )
