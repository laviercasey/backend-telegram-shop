from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.crud.base import CRUDBase
from app.models.product import Product, ProductImage
from app.schemas.product import ProductCreate, ProductUpdate, ProductImageCreate, ProductImageUpdate


class CRUDProduct(CRUDBase[Product, ProductCreate, ProductUpdate]):
    def get_by_shop(
        self, db: Session, *, shop_id: int, skip: int = 0, limit: int = 100
    ) -> List[Product]:
        return (
            db.query(self.model)
            .filter(Product.shop_id == shop_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_category(
        self, db: Session, *, category_id: int, skip: int = 0, limit: int = 100
    ) -> List[Product]:
        return (
            db.query(self.model)
            .filter(Product.category_id == category_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search(
        self, db: Session, *, shop_id: int, query: str, skip: int = 0, limit: int = 100
    ) -> List[Product]:
        return (
            db.query(self.model)
            .filter(
                Product.shop_id == shop_id,
                Product.name.ilike(f"%{query}%")
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_with_shop(
        self, db: Session, *, obj_in: ProductCreate, shop_id: int
    ) -> Product:
        obj_in_data = obj_in.model_dump()
        obj_in_data["shop_id"] = shop_id
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_with_images(self, db: Session, *, id: int) -> Optional[Product]:
        return db.query(Product).filter(Product.id == id).first()


class CRUDProductImage(CRUDBase[ProductImage, ProductImageCreate, ProductImageUpdate]):
    def get_by_product(
        self, db: Session, *, product_id: int
    ) -> List[ProductImage]:
        return (
            db.query(self.model)
            .filter(ProductImage.product_id == product_id)
            .order_by(ProductImage.order)
            .all()
        )

    def get_primary(
        self, db: Session, *, product_id: int
    ) -> Optional[ProductImage]:
        return (
            db.query(self.model)
            .filter(ProductImage.product_id == product_id, ProductImage.is_primary == True)
            .first()
        )

    def create_with_product(
        self, db: Session, *, obj_in: ProductImageCreate, product_id: int
    ) -> ProductImage:
        obj_in_data = obj_in.model_dump()
        obj_in_data["product_id"] = product_id
        
        if obj_in_data.get("is_primary"):
            existing_primary = self.get_primary(db=db, product_id=product_id)
            if existing_primary:
                existing_primary.is_primary = False
                db.add(existing_primary)
        
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


product = CRUDProduct(Product)
product_image = CRUDProductImage(ProductImage)
