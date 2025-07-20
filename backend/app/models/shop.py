from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.session import Base


class Shop(Base):
    __tablename__ = "shops"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    welcome_message = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    logo_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    owner = relationship("User", back_populates="shops")
    products = relationship("Product", back_populates="shop")
    categories = relationship("Category", back_populates="shop")
    orders = relationship("Order", back_populates="shop")
    settings = relationship("ShopSettings", back_populates="shop", uselist=False)


class ShopSettings(Base):
    __tablename__ = "shop_settings"

    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), unique=True)
    currency = Column(String, default="USD")
    language = Column(String, default="en")
    theme = Column(String, default="default")
    features = Column(String, default='{"analytics":true,"notifications":true,"multilingual":false,"discounts":true,"loyalty":true,"order_history":true,"reviews":true}')
    payment_providers = Column(String, default='{"stripe":false,"paypal":false,"yookassa":false}')
    
    shop = relationship("Shop", back_populates="settings")
