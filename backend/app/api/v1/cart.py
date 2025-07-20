from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user
from backend.app.crud.cart import cart_item as cart_item_crud
from backend.app.crud.product import product as product_crud
from app.models.user import User
from app.schemas.cart import CartItem, CartItemCreate, CartItemUpdate, CartItemWithProduct, Cart

router = APIRouter()

@router.get("/", response_model=Cart)
def read_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    items = cart_item_crud.get_by_user(db=db, user_id=current_user.id)
    
    totals = cart_item_crud.get_cart_totals(db=db, user_id=current_user.id)
    
    return {
        "items": items,
        "total_items": totals["total_items"],
        "total_price": totals["total_price"]
    }

@router.post("/items", response_model=CartItem)
def add_to_cart(
    item_in: CartItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    product = product_crud.get(db=db, id=item_in.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if not product.is_available or product.stock < item_in.quantity:
        raise HTTPException(status_code=400, detail="Product not available in requested quantity")
    
    item_in.user_id = current_user.id
    item_in.price = product.discount_price if product.discount_price else product.price
    
    item = cart_item_crud.create_or_update(db=db, obj_in=item_in)
    return item

@router.put("/items/{item_id}", response_model=CartItem)
def update_cart_item(
    item_id: int,
    item_in: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    item = cart_item_crud.get(db=db, id=item_id)
    if not item or item.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    product = product_crud.get(db=db, id=item.product_id)
    if not product.is_available or (item_in.quantity and product.stock < item_in.quantity):
        raise HTTPException(status_code=400, detail="Product not available in requested quantity")
    
    item = cart_item_crud.update(db=db, db_obj=item, obj_in=item_in)
    return item

@router.delete("/items/{item_id}")
def remove_from_cart(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    item = cart_item_crud.get(db=db, id=item_id)
    if not item or item.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    cart_item_crud.remove(db=db, id=item_id)
    return {"status": "success"}

@router.delete("/")
def clear_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    cart_item_crud.clear_cart(db=db, user_id=current_user.id)
    return {"status": "success"}
