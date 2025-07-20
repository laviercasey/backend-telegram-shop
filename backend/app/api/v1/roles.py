# app/api/v1/roles.py
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_shop_owner
from backend.app.crud.user import user as user_crud, role as role_crud
from app.models.user import User
from app.schemas.user import Role, UserRole, UserRoleCreate

router = APIRouter()

@router.get("/", response_model=List[Role])
def read_roles(
    db: Session = Depends(get_db),
) -> Any:
    roles = role_crud.get_multi(db=db)
    return roles

@router.post("/users/{user_id}/roles", response_model=UserRole)
def assign_role_to_user(
    user_id: int,
    user_role: UserRoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_shop_owner),
) -> Any:
    user = user_crud.get(db=db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    role = role_crud.get(db=db, id=user_role.role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    
    user_role = user_crud.add_role_to_user(
        db=db, 
        user_id=user_id, 
        role_id=user_role.role_id, 
        shop_id=user_role.shop_id
    )
    
    return user_role

@router.delete("/users/{user_id}/roles/{role_id}")
def remove_role_from_user(
    user_id: int,
    role_id: int,
    shop_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_shop_owner),
) -> Any:
    user = user_crud.get(db=db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    role = role_crud.get(db=db, id=role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    
    user_crud.remove_role_from_user(
        db=db, 
        user_id=user_id, 
        role_id=role_id, 
        shop_id=shop_id
    )
    
    return {"status": "success"}
