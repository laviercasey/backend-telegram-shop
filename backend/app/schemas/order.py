from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

from app.schemas.base import BaseSchema
from app.schemas.product import Product
from app.models.order import OrderStatus


class OrderItemBase(BaseSchema):
    product_id: int
    quantity: int
    price: float


class OrderItemCreate(OrderItemBase):
    pass


class OrderItem(OrderItemBase):
    id: int
    order_id: int


class OrderItemWithProduct(OrderItem):
    product: Product


class OrderBase(BaseSchema):
    order_number: str
    total_amount: float
    shipping_address: Optional[str] = None
    shipping_method: Optional[str] = None
    shipping_cost: float = 0
    payment_method: Optional[str] = None


class OrderCreate(BaseSchema):
    user_id: int
    shop_id: int
    items: List[OrderItemCreate]
    shipping_address: Optional[str] = None
    shipping_method: Optional[str] = None
    payment_method: str


class OrderUpdate(BaseSchema):
    status: Optional[OrderStatus] = None
    shipping_address: Optional[str] = None
    shipping_method: Optional[str] = None
    shipping_cost: Optional[float] = None
    payment_method: Optional[str] = None
    payment_id: Optional[str] = None


class Order(OrderBase):
    id: int
    user_id: int
    shop_id: int
    status: OrderStatus
    payment_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class OrderWithItems(Order):
    items: List[OrderItemWithProduct] = []
