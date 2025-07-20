from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user, get_shop_manager
from backend.app.crud.category import category as category_crud
from app.models.user import User
from app.schemas.category import Category, CategoryCreate, CategoryUpdate, CategoryWithChildren

router = APIRouter()

@router.get("/shop/{shop_id}", response_model=List[CategoryWithChildren])
def read_categories(
    shop_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> Any:
    categories = category_crud.get_by_shop(
        db=db, shop_id=shop_id, skip=skip, limit=limit
    )
    return categories

@router.post("/shop/{shop_id}", response_model=Category)
def create_category(
    shop_id: int,
    category_in: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_shop_manager),
) -> Any:
    category = category_crud.create_with_shop(
        db=db, obj_in=category_in, shop_id=shop_id
    )
    return category

@router.get("/{category_id}", response_model=Category)
def read_category(
    category_id: int,
    db: Session = Depends(get_db),
) -> Any:
    category = category_crud.get(db=db, id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return category

@router.put("/{category_id}", response_model=Category)
def update_category(
    category_id: int,
    category_in: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_shop_manager),
) -> Any:
    category = category_crud.get(db=db, id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    category = category_crud.update(db=db, db_obj=category, obj_in=category_in)
    return category

@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_shop_manager),
) -> Any:
    category = category_crud.get(db=db, id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    category = category_crud.remove(db=db, id=category_id)
    return {"status": "success"}

@router.get("/{category_id}/subcategories", response_model=List[Category])
def read_subcategories(
    category_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> Any:
    subcategories = category_crud.get_subcategories(
        db=db, parent_id=category_id, skip=skip, limit=limit
    )
    return subcategories

@router.post("/{category_id}/image", response_model=Category)
def upload_category_image(
    category_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_shop_manager),
) -> Any:
    category = category_crud.get(db=db, id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Логика загрузки файла и получения URL
    image_url = f"/uploads/categories/{category_id}/{file.filename}"
    
    category = category_crud.update(db=db, db_obj=category, obj_in={"image_url": image_url})
    return category
