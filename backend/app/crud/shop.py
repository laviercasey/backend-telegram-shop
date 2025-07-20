from typing import Any, Dict, Optional, Union, List
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.shop import Shop, ShopSettings
from app.schemas.shop import ShopCreate, ShopUpdate, ShopSettingsCreate, ShopSettingsUpdate


class CRUDShop(CRUDBase[Shop, ShopCreate, ShopUpdate]):
    def get_multi_by_owner(
        self, db: Session, *, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[Shop]:
        return (
            db.query(self.model)
            .filter(Shop.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_with_owner(
        self, db: Session, *, obj_in: ShopCreate, owner_id: int
    ) -> Shop:
        obj_in_data = obj_in.model_dump()
        obj_in_data["owner_id"] = owner_id
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        
        settings = ShopSettings(shop_id=db_obj.id)
        db.add(settings)
        db.commit()
        
        return db_obj

    def get_shop_with_settings(self, db: Session, *, shop_id: int) -> Optional[Shop]:
        return db.query(Shop).filter(Shop.id == shop_id).first()


class CRUDShopSettings(CRUDBase[ShopSettings, ShopSettingsCreate, ShopSettingsUpdate]):
    def get_by_shop_id(self, db: Session, *, shop_id: int) -> Optional[ShopSettings]:
        return db.query(ShopSettings).filter(ShopSettings.shop_id == shop_id).first()

    def update_features(
        self, db: Session, *, db_obj: ShopSettings, features: Dict[str, bool]
    ) -> ShopSettings:
        current_features = db_obj.features
        if isinstance(current_features, str):
            import json
            current_features = json.loads(current_features)
        
        current_features.update(features)
        db_obj.features = current_features
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_payment_providers(
        self, db: Session, *, db_obj: ShopSettings, providers: Dict[str, bool]
    ) -> ShopSettings:
        current_providers = db_obj.payment_providers
        if isinstance(current_providers, str):
            import json
            current_providers = json.loads(current_providers)
        
        current_providers.update(providers)
        db_obj.payment_providers = current_providers
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


shop = CRUDShop(Shop)
shop_settings = CRUDShopSettings(ShopSettings)
