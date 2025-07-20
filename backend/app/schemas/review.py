from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from app.schemas.base import BaseSchema
from app.schemas.user import User


class ReviewBase(BaseSchema):
    product_id: int
    rating: float = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class ReviewCreate(ReviewBase):
    user_id: int


class ReviewUpdate(BaseSchema):
    rating: Optional[float] = Field(None, ge=1, le=5)
    comment: Optional[str] = None


class Review(ReviewBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


class ReviewWithUser(Review):
    user: User
