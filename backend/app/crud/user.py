from typing import Any, Dict, Optional, Union, List
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.user import User, Role, UserRole
from app.schemas.user import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_telegram_id(self, db: Session, *, telegram_id: str) -> Optional[User]:
        return db.query(User).filter(User.telegram_id == telegram_id).first()

    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        db_obj = User(
            telegram_id=obj_in.telegram_id,
            username=obj_in.username,
            first_name=obj_in.first_name,
            last_name=obj_in.last_name,
            email=obj_in.email,
            phone=obj_in.phone,
            is_active=True,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_user_roles(self, db: Session, *, user_id: int, shop_id: Optional[int] = None) -> List[UserRole]:
        query = db.query(UserRole).filter(UserRole.user_id == user_id)
        if shop_id:
            query = query.filter(UserRole.shop_id == shop_id)
        return query.all()

    def add_role_to_user(
        self, db: Session, *, user_id: int, role_id: int, shop_id: Optional[int] = None
    ) -> UserRole:
        db_obj = UserRole(user_id=user_id, role_id=role_id, shop_id=shop_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove_role_from_user(
        self, db: Session, *, user_id: int, role_id: int, shop_id: Optional[int] = None
    ) -> None:
        query = db.query(UserRole).filter(
            UserRole.user_id == user_id, 
            UserRole.role_id == role_id
        )
        if shop_id:
            query = query.filter(UserRole.shop_id == shop_id)
        
        user_role = query.first()
        if user_role:
            db.delete(user_role)
            db.commit()


class CRUDRole(CRUDBase[Role, Any, Any]):
    def get_by_name(self, db: Session, *, name: str) -> Optional[Role]:
        return db.query(Role).filter(Role.name == name).first()


user = CRUDUser(User)
role = CRUDRole(Role)
