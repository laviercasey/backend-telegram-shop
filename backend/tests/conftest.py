import os
import pytest
from typing import Dict, Generator, Any
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta

from app.db.base import Base
from app.db.session import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import User, Role, UserRole
from app.models.shop import Shop, ShopSettings
from app.models.category import Category
from app.models.product import Product
from app.models.order import Order, OrderItem, OrderStatus
from backend.app.crud.user import user as user_crud
from main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides = {}

@pytest.fixture
def test_user(db: Session) -> User:
    user_data = {
        "telegram_id": "12345678",
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "is_active": True
    }
    user = User(**user_data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def test_admin_role(db: Session) -> Role:
    role = Role(name="admin", description="Administrator role")
    db.add(role)
    db.commit()
    db.refresh(role)
    return role

@pytest.fixture
def test_shop(db: Session, test_user: User) -> Shop:
    shop = Shop(
        name="Test Shop",
        description="Test Shop Description",
        welcome_message="Welcome to Test Shop!",
        owner_id=test_user.id,
        is_active=True
    )
    db.add(shop)
    db.commit()
    db.refresh(shop)
    
    settings = ShopSettings(
        shop_id=shop.id,
        currency="USD",
        language="en",
        theme="default",
        features='{"analytics":true,"notifications":true}',
        payment_providers='{"stripe":true,"paypal":false}'
    )
    db.add(settings)
    db.commit()
    
    return shop

@pytest.fixture
def test_category(db: Session, test_shop: Shop) -> Category:
    category = Category(
        name="Test Category",
        description="Test Category Description",
        shop_id=test_shop.id
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category

@pytest.fixture
def test_product(db: Session, test_shop: Shop, test_category: Category) -> Product:
    product = Product(
        name="Test Product",
        description="Test Product Description",
        price=99.99,
        stock=10,
        is_available=True,
        shop_id=test_shop.id,
        category_id=test_category.id
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

@pytest.fixture
def test_order(db: Session, test_user: User, test_shop: Shop, test_product: Product) -> Order:
    order = Order(
        user_id=test_user.id,
        shop_id=test_shop.id,
        order_number="ORD-12345",
        status=OrderStatus.PENDING,
        total_amount=99.99,
        payment_method="credit_card"
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    order_item = OrderItem(
        order_id=order.id,
        product_id=test_product.id,
        quantity=1,
        price=99.99
    )
    db.add(order_item)
    db.commit()
    
    return order

@pytest.fixture
def user_token_headers(test_user: User) -> Dict[str, str]:
    access_token = create_access_token(
        subject=test_user.telegram_id,
        expires_delta=timedelta(minutes=60)
    )
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
def mock_telegram_auth_data() -> Dict[str, Any]:
    return {
        "id": 12345678,
        "first_name": "Test",
        "last_name": "User",
        "username": "testuser",
        "photo_url": None,
        "auth_date": int(datetime.now().timestamp()),
        "hash": "fake_hash_for_testing"  # В тестах будем мокать проверку хеша
    }
