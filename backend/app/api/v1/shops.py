from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user, get_shop_owner, get_shop_admin
from app.crud.shop import shop as shop_crud, shop_settings as shop_settings_crud
from app.models.user import User
from app.schemas.shop import Shop, ShopCreate, ShopUpdate, ShopSettings, ShopSettingsUpdate, ShopWithSettings

router = APIRouter()

@router.get("/", response_model=List[Shop])
def read_shops(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    shops = shop_crud.get_multi_by_owner(
        db=db, owner_id=current_user.id, skip=skip, limit=limit
    )
    return shops

@router.post("/", response_model=Shop)
def create_shop(
    shop_in: ShopCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    shop = shop_crud.create_with_owner(
        db=db, obj_in=shop_in, owner_id=current_user.id
    )
    return shop

@router.get("/{shop_id}", response_model=ShopWithSettings)
def read_shop(
    shop_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    shop = shop_crud.get_shop_with_settings(db=db, shop_id=shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    if shop.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return shop

@router.put("/{shop_id}", response_model=Shop)
def update_shop(
    shop_id: int,
    shop_in: ShopUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_shop_owner),
) -> Any:
    shop = shop_crud.get(db=db, id=shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    shop = shop_crud.update(db=db, db_obj=shop, obj_in=shop_in)
    return shop

@router.delete("/{shop_id}")
def delete_shop(
    shop_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_shop_owner),
) -> Any:
    shop = shop_crud.get(db=db, id=shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    shop = shop_crud.remove(db=db, id=shop_id)
    return {"status": "success"}

@router.post("/{shop_id}/logo", response_model=Shop)
def upload_shop_logo(
    shop_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_shop_owner),
) -> Any:
    shop = shop_crud.get(db=db, id=shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    logo_url = f"/uploads/{shop_id}/{file.filename}"
    
    shop = shop_crud.update(db=db, db_obj=shop, obj_in={"logo_url": logo_url})
    return shop

@router.get("/{shop_id}/settings", response_model=ShopSettings)
def read_shop_settings(
    shop_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_shop_admin),
) -> Any:
    settings = shop_settings_crud.get_by_shop_id(db=db, shop_id=shop_id)
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    
    return settings

@router.put("/{shop_id}/settings", response_model=ShopSettings)
def update_shop_settings(
    shop_id: int,
    settings_in: ShopSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_shop_owner),
) -> Any:
    settings = shop_settings_crud.get_by_shop_id(db=db, shop_id=shop_id)
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    
    settings = shop_settings_crud.update(db=db, db_obj=settings, obj_in=settings_in)
    return settings

@router.put("/{shop_id}/features", response_model=ShopSettings)
def update_shop_features(
    shop_id: int,
    features: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_shop_owner),
) -> Any:
    settings = shop_settings_crud.get_by_shop_id(db=db, shop_id=shop_id)
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    
    settings = shop_settings_crud.update_features(db=db, db_obj=settings, features=features)
    return settings

@router.put("/{shop_id}/payment-providers", response_model=ShopSettings)
def update_payment_providers(
    shop_id: int,
    providers: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_shop_owner),
) -> Any:
    settings = shop_settings_crud.get_by_shop_id(db=db, shop_id=shop_id)
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    
    settings = shop_settings_crud.update_payment_providers(db=db, db_obj=settings, providers=providers)
    return settings
