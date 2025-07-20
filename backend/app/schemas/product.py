# app/schemas/product.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.schemas.base import BaseSchema
from app.schemas.category import Category


class ProductImageBase(BaseSchema):
    image_url: str
    is_primary: bool = False
    order: int = 0


class ProductImageCreate(ProductImageBase):
    product_id: int


class ProductImageUpdate(BaseSchema):
    image_url: Optional[str] = None
    is_primary: Optional[bool] = None
    order: Optional[int] = None


class ProductImage(ProductImageBase):
    id: int
    product_id: int


class ProductBase(BaseSchema):
    name: str
    description: Optional[str] = None
    price: float
    discount_price: Optional[float] = None
    sku: Optional[str] = None
    stock: int = 0
    is_available: bool = True
    category_id: Optional[int] = None


class ProductCreate(ProductBase):
    shop_id: int


class ProductUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    discount_price: Optional[float] = None
    sku: Optional[str] = None
    stock: Optional[int] = None
    is_available: Optional[bool] = None
    category_id: Optional[int] = None


class ProductInDB(ProductBase):
    id: int
    shop_id: int
    created_at: datetime
    updated_at: datetime


class Product(ProductInDB):
    pass


class ProductWithImages(Product):
    images: List[ProductImage] = []


class ProductWithCategory(ProductWithImages):
    category: Optional[Category] = None
