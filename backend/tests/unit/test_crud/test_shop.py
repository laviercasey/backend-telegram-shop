import pytest
import json
from sqlalchemy.orm import Session

from backend.app.crud.shop import shop as shop_crud, shop_settings as shop_settings_crud
from app.models.shop import Shop, ShopSettings
from app.schemas.shop import ShopCreate, ShopUpdate, ShopSettingsUpdate

def test_create_shop(db: Session, test_user: User):
    shop_in = ShopCreate(
        name="New Test Shop",
        description="New Test Shop Description",
        welcome_message="Welcome!",
        owner_id=test_user.id
    )
    
    shop = shop_crud.create_with_owner(db=db, obj_in=shop_in, owner_id=test_user.id)
    
    assert shop.name == "New Test Shop"
    assert shop.description == "New Test Shop Description"
    assert shop.owner_id == test_user.id
    assert shop.is_active is True

    settings = shop_settings_crud.get_by_shop_id(db=db, shop_id=shop.id)
    assert settings is not None
    assert settings.shop_id == shop.id

def test_get_shop(db: Session, test_shop: Shop):
    shop = shop_crud.get(db=db, id=test_shop.id)
    assert shop
    assert shop.name == test_shop.name
    assert shop.owner_id == test_shop.owner_id

def test_get_multi_by_owner(db: Session, test_user: User, test_shop: Shop):
    shop_in = ShopCreate(
        name="Second Shop",
        description="Second Shop Description",
        owner_id=test_user.id
    )
    shop_crud.create_with_owner(db=db, obj_in=shop_in, owner_id=test_user.id)

    shops = shop_crud.get_multi_by_owner(db=db, owner_id=test_user.id)
    assert len(shops) == 2
    assert shops[0].name == test_shop.name
    assert shops[1].name == "Second Shop"

def test_update_shop(db: Session, test_shop: Shop):
    shop_update = ShopUpdate(
        name="Updated Shop Name",
        description="Updated Description"
    )
    
    updated_shop = shop_crud.update(db=db, db_obj=test_shop, obj_in=shop_update)
    
    assert updated_shop.name == "Updated Shop Name"
    assert updated_shop.description == "Updated Description"
    assert updated_shop.id == test_shop.id

def test_update_shop_settings(db: Session, test_shop: Shop):
    settings = shop_settings_crud.get_by_shop_id(db=db, shop_id=test_shop.id)
    
    settings_update = ShopSettingsUpdate(
        currency="EUR",
        language="fr"
    )
    
    updated_settings = shop_settings_crud.update(
        db=db, db_obj=settings, obj_in=settings_update
    )
    
    assert updated_settings.currency == "EUR"
    assert updated_settings.language == "fr"

def test_update_shop_features(db: Session, test_shop: Shop):
    settings = shop_settings_crud.get_by_shop_id(db=db, shop_id=test_shop.id)
 
    new_features = {
        "analytics": False,
        "multilingual": True
    }
    
    updated_settings = shop_settings_crud.update_features(
        db=db, db_obj=settings, features=new_features
    )

    features = json.loads(updated_settings.features)
    assert features["analytics"] is False
    assert features["multilingual"] is True
    assert features["notifications"] is True
