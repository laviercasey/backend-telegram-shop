from pydantic import BaseModel
from typing import Optional

from app.schemas.base import BaseSchema
from app.schemas.user import User


class Token(BaseSchema):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseSchema):
    sub: str
    exp: int


class TelegramAuth(BaseSchema):
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: int
    hash: str


class AuthResponse(BaseSchema):
    token: Token
    user: User
