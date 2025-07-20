from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

from app.schemas.base import BaseSchema


class RoleBase(BaseSchema):
    name: str
    description: Optional[str] = None


class RoleCreate(RoleBase):
    pass


class RoleUpdate(RoleBase):
    pass


class Role(RoleBase):
    id: int


class UserRoleBase(BaseSchema):
    role_id: int
    shop_id: Optional[int] = None


class UserRoleCreate(UserRoleBase):
    user_id: int


class UserRoleUpdate(UserRoleBase):
    pass


class UserRole(UserRoleBase):
    id: int
    user_id: int
    role: Role


class UserBase(BaseSchema):
    telegram_id: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class UserCreate(UserBase):
    pass


class UserUpdate(BaseSchema):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class User(UserInDB):
    pass


class UserWithRoles(User):
    roles: List[UserRole] = []
