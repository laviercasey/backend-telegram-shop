from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user, get_shop_admin
from backend.app.crud.user import user as user_crud
from app.models.user import User
from app.schemas.user import User as UserSchema, UserCreate, UserUpdate, UserWithRoles

router = APIRouter()

@router.get("/me", response_model=UserSchema)
def read_user_me(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    return current_user

@router.put("/me", response_model=UserSchema)
def update_user_me(
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    user = user_crud.update(db=db, db_obj=current_user, obj_in=user_in)
    return user

@router.get("/shop/{shop_id}/users", response_model=List[UserWithRoles])
def read_shop_users(
    shop_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_shop_admin),
) -> Any:
    return []
