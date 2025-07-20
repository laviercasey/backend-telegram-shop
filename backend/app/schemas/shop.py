from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.schemas.base import BaseSchema
from app.schemas.user import User


class ShopSettingsBase(BaseSchema):
    currency: str = "USD"
    language: str = "en"
    theme: str = "default"
    features: Dict[str, bool] = Field(
        default_factory=lambda: {
            "analytics": True,
            "notifications": True,
            "multilingual": False,
            "discounts": True,
            "loyalty": True,
            "order_history": True,
            "reviews": True
        }
    )
    payment_providers: Dict[str, bool] = Field(
        default_factory=lambda: {
            "stripe": False,
            "paypal": False,
            "yookassa": False
        }
    )


class ShopSettingsCreate(ShopSettingsBase):
    shop_id: int


class ShopSettingsUpdate(BaseSchema):
    currency: Optional[str] = None
    language: Optional[str] = None
    theme: Optional[str] = None
    features: Optional[Dict[str, bool]] = None
    payment_providers: Optional[Dict[str, bool]] = None


class ShopSettings(ShopSettingsBase):
    id: int
    shop_id: int


class ShopBase(BaseSchema):
    name: str
    description: Optional[str] = None
    welcome_message: Optional[str] = None
    logo_url: Optional[str] = None


class ShopCreate(ShopBase):
    owner_id: int


class ShopUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    welcome_message: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: Optional[bool] = None


class ShopInDB(ShopBase):
    id: int
    owner_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class Shop(ShopInDB):
    pass


class ShopWithSettings(Shop):
    settings: ShopSettings


class ShopWithOwner(Shop):
    owner: User
