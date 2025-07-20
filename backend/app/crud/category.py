from typing import List, Optional
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


class CRUDCategory(CRUDBase[Category, CategoryCreate, CategoryUpdate]):
    def get_by_shop(
        self, db: Session, *, shop_id: int, skip: int = 0, limit: int = 100
    ) -> List[Category]:
        return (
            db.query(self.model)
            .filter(Category.shop_id == shop_id, Category.parent_id == None)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_subcategories(
        self, db: Session, *, parent_id: int, skip: int = 0, limit: int = 100
    ) -> List[Category]:
        return (
            db.query(self.model)
            .filter(Category.parent_id == parent_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_with_shop(
        self, db: Session, *, obj_in: CategoryCreate, shop_id: int
    ) -> Category:
        obj_in_data = obj_in.model_dump()
        obj_in_data["shop_id"] = shop_id
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


category = CRUDCategory(Category)
