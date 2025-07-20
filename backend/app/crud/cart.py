from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.crud.base import CRUDBase
from app.models.cart import CartItem
from app.schemas.cart import CartItemCreate, CartItemUpdate


class CRUDCartItem(CRUDBase[CartItem, CartItemCreate, CartItemUpdate]):
    def get_by_user(
        self, db: Session, *, user_id: int
    ) -> List[CartItem]:
        return (
            db.query(self.model)
            .filter(CartItem.user_id == user_id)
            .all()
        )

    def get_by_user_and_product(
        self, db: Session, *, user_id: int, product_id: int
    ) -> Optional[CartItem]:
        return (
            db.query(self.model)
            .filter(CartItem.user_id == user_id, CartItem.product_id == product_id)
            .first()
        )

    def create_or_update(
        self, db: Session, *, obj_in: CartItemCreate
    ) -> CartItem:
        existing_item = self.get_by_user_and_product(
            db=db, user_id=obj_in.user_id, product_id=obj_in.product_id
        )
        
        if existing_item:
            existing_item.quantity += obj_in.quantity
            db.add(existing_item)
            db.commit()
            db.refresh(existing_item)
            return existing_item
        else:
            return self.create(db=db, obj_in=obj_in)

    def get_cart_totals(
        self, db: Session, *, user_id: int
    ) -> dict:
        total_items = db.query(func.sum(CartItem.quantity)).filter(
            CartItem.user_id == user_id
        ).scalar() or 0
        
        total_price = db.query(func.sum(CartItem.price * CartItem.quantity)).filter(
            CartItem.user_id == user_id
        ).scalar() or 0
        
        return {
            "total_items": total_items,
            "total_price": total_price
        }

    def clear_cart(
        self, db: Session, *, user_id: int
    ) -> None:
        db.query(self.model).filter(CartItem.user_id == user_id).delete()
        db.commit()


cart_item = CRUDCartItem(CartItem)
