from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user, get_shop_manager
from backend.app.crud.product import product as product_crud, product_image as product_image_crud
from app.models.user import User
from app.schemas.product import (
    Product, ProductCreate, ProductUpdate, ProductImage, 
    ProductImageCreate, ProductWithImages, ProductWithCategory
)

router = APIRouter()

@router.get("/shop/{shop_id}", response_model=List[ProductWithImages])
def read_products(
    shop_id: int,
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[int] = None,
    db: Session = Depends(get_db),
) -> Any:
    if category_id:
        products = product_crud.get_by_category(
            db=db, category_id=category_id, skip=skip, limit=limit
        )
    else:
        products = product_crud.get_by_shop(
            db=db, shop_id=shop_id, skip=skip, limit=limit
        )
    return products

@router.post("/shop/{shop_id}", response_model=Product)
def create_product(
    shop_id: int,
    product_in: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_shop_manager),
) -> Any:
    product = product_crud.create_with_shop(
        db=db, obj_in=product_in, shop_id=shop_id
    )
    return product

@router.get("/{product_id}", response_model=ProductWithCategory)
def read_product(
    product_id: int,
    db: Session = Depends(get_db),
) -> Any:
    product = product_crud.get_with_images(db=db, id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product

@router.put("/{product_id}", response_model=Product)
def update_product(
    product_id: int,
    product_in: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_shop_manager),
) -> Any:
    product = product_crud.get(db=db, id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = product_crud.update(db=db, db_obj=product, obj_in=product_in)
    return product

@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_shop_manager),
) -> Any:
    product = product_crud.get(db=db, id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = product_crud.remove(db=db, id=product_id)
    return {"status": "success"}

@router.get("/{product_id}/images", response_model=List[ProductImage])
def read_product_images(
    product_id: int,
    db: Session = Depends(get_db),
) -> Any:
    images = product_image_crud.get_by_product(db=db, product_id=product_id)
    return images

@router.post("/{product_id}/images", response_model=ProductImage)
def upload_product_image(
    product_id: int,
    is_primary: bool = Form(False),
    order: int = Form(0),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_shop_manager),
) -> Any:
    product = product_crud.get(db=db, id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    image_url = f"/uploads/products/{product_id}/{file.filename}"
    
    image_in = ProductImageCreate(
        product_id=product_id,
        image_url=image_url,
        is_primary=is_primary,
        order=order
    )
    
    image = product_image_crud.create_with_product(
        db=db, obj_in=image_in, product_id=product_id
    )
    return image

@router.delete("/images/{image_id}")
def delete_product_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_shop_manager),
) -> Any:
    image = product_image_crud.get(db=db, id=image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    image = product_image_crud.remove(db=db, id=image_id)
    return {"status": "success"}

@router.get("/search/{shop_id}", response_model=List[ProductWithImages])
def search_products(
    shop_id: int,
    query: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> Any:
    products = product_crud.search(
        db=db, shop_id=shop_id, query=query, skip=skip, limit=limit
    )
    return products
