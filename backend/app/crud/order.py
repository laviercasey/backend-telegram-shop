from typing import List, Optional
from sqlalchemy.orm import Session
import uuid

from app.crud.base import CRUDBase
from app.models.order import Order, OrderItem, OrderStatus
from app.schemas.order import OrderCreate, OrderUpdate, OrderItemCreate


class CRUDOrderItem(CRUDBase[OrderItem, OrderItemCreate, any]):
    def get_by_order(
        self, db: Session, *, order_id: int
    ) -> List[OrderItem]:
        return (
            db.query(self.model)
            .filter(OrderItem.order_id == order_id)
            .all()
        )

    def create_with_order(
        self, db: Session, *, obj_in: OrderItemCreate, order_id: int
    ) -> OrderItem:
        obj_in_data = obj_in.model_dump()
        obj_in_data["order_id"] = order_id
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


class CRUDOrder(CRUDBase[Order, OrderCreate, OrderUpdate]):
    def get_by_user(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Order]:
        return (
            db.query(self.model)
            .filter(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_shop(
        self, db: Session, *, shop_id: int, skip: int = 0, limit: int = 100
    ) -> List[Order]:
        return (
            db.query(self.model)
            .filter(Order.shop_id == shop_id)
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_shop_and_status(
        self, db: Session, *, shop_id: int, status: OrderStatus, skip: int = 0, limit: int = 100
    ) -> List[Order]:
        return (
            db.query(self.model)
            .filter(Order.shop_id == shop_id, Order.status == status)
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_with_items(
        self, db: Session, *, obj_in: OrderCreate
    ) -> Order:
        order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        
        total_amount = sum(item.price * item.quantity for item in obj_in.items)
        
        db_obj = Order(
            user_id=obj_in.user_id,
            shop_id=obj_in.shop_id,
            order_number=order_number,
            total_amount=total_amount,
            shipping_address=obj_in.shipping_address,
            shipping_method=obj_in.shipping_method,
            payment_method=obj_in.payment_method,
            status=OrderStatus.PENDING
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        
        for item in obj_in.items:
            order_item = OrderItem(
                order_id=db_obj.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.price
            )
            db.add(order_item)
        
        db.commit()
        return db_obj

    def update_status(
        self, db: Session, *, order_id: int, status: OrderStatus
    ) -> Order:
        db_obj = self.get(db=db, id=order_id)
        if db_obj:
            db_obj.status = status
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
        return db_obj


order = CRUDOrder(Order)
order_item = CRUDOrderItem(OrderItem)
