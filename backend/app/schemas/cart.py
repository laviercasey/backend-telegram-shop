from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.schemas.base import BaseSchema
from app.schemas.product import Product


class CartItemBase(BaseSchema):
    product_id: int
    quantity: int = 1
    price: float


class CartItemCreate(CartItemBase):
    user_id: int


class CartItemUpdate(BaseSchema):
    quantity: Optional[int] = None
    price: Optional[float] = None


class CartItem(CartItemBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


class CartItemWithProduct(CartItem):
    product: Product


class Cart(BaseSchema):
    items: List[CartItemWithProduct] = []
    total_items: int = 0
    total_price: float = 0.0
