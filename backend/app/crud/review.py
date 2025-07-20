from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.crud.base import CRUDBase
from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewUpdate


class CRUDReview(CRUDBase[Review, ReviewCreate, ReviewUpdate]):
    def get_by_product(
        self, db: Session, *, product_id: int, skip: int = 0, limit: int = 100
    ) -> List[Review]:
        return (
            db.query(self.model)
            .filter(Review.product_id == product_id)
            .order_by(Review.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_user_and_product(
        self, db: Session, *, user_id: int, product_id: int
    ) -> Optional[Review]:
        return (
            db.query(self.model)
            .filter(Review.user_id == user_id, Review.product_id == product_id)
            .first()
        )

    def get_product_rating(
        self, db: Session, *, product_id: int
    ) -> dict:
        avg_rating = db.query(func.avg(Review.rating)).filter(
            Review.product_id == product_id
        ).scalar() or 0
        
        count = db.query(func.count(Review.id)).filter(
            Review.product_id == product_id
        ).scalar() or 0
        
        return {
            "average": float(avg_rating),
            "count": count
        }


review = CRUDReview(Review)
