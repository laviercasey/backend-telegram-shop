from typing import List, Optional
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.payment import Payment, PaymentStatus
from app.schemas.payment import PaymentCreate, PaymentUpdate


class CRUDPayment(CRUDBase[Payment, PaymentCreate, PaymentUpdate]):
    def get_by_order(
        self, db: Session, *, order_id: int
    ) -> Optional[Payment]:
        return (
            db.query(self.model)
            .filter(Payment.order_id == order_id)
            .first()
        )

    def get_by_provider_payment_id(
        self, db: Session, *, provider_payment_id: str
    ) -> Optional[Payment]:
        return (
            db.query(self.model)
            .filter(Payment.provider_payment_id == provider_payment_id)
            .first()
        )

    def update_status(
        self, db: Session, *, payment_id: int, status: PaymentStatus, details: Optional[str] = None
    ) -> Payment:
        db_obj = self.get(db=db, id=payment_id)
        if db_obj:
            db_obj.status = status
            if details:
                db_obj.details = details
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
        return db_obj


payment = CRUDPayment(Payment)
