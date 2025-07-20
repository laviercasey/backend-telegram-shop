from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.schemas.base import BaseSchema


class CategoryBase(BaseSchema):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    parent_id: Optional[int] = None


class CategoryCreate(CategoryBase):
    shop_id: int


class CategoryUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    parent_id: Optional[int] = None


class CategoryInDB(CategoryBase):
    id: int
    shop_id: int
    created_at: datetime
    updated_at: datetime


class Category(CategoryInDB):
    pass


class CategoryWithChildren(Category):
    subcategories: List['CategoryWithChildren'] = []
