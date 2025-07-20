from sqlalchemy.orm import Session

from app.db.session import Base, engine
from app.core.config import settings
from app.db.init_roles import init_roles

from app.models.user import User, Role, UserRole
from app.models.shop import Shop, ShopSettings
from app.models.category import Category
from app.models.product import Product, ProductImage
from app.models.cart import CartItem
from app.models.order import Order, OrderItem
from app.models.payment import Payment
from app.models.review import Review


def init_db(db: Session) -> None:
    Base.metadata.create_all(bind=engine)
    
    init_roles(db)
