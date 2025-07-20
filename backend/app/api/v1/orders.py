from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user, get_shop_admin
from backend.app.crud.order import order as order_crud
from backend.app.crud.cart import cart_item as cart_item_crud
from app.models.user import User
from app.models.order import OrderStatus
from app.schemas.order import Order, OrderCreate, OrderUpdate, OrderWithItems

router = APIRouter()

@router.get("/my", response_model=List[Order])
def read_user_orders(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    orders = order_crud.get_by_user(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )
    return orders

@router.get("/shop/{shop_id}", response_model=List[Order])
def read_shop_orders(
    shop_id: int,
    status: Optional[OrderStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_shop_admin),
) -> Any:
    if status:
        orders = order_crud.get_by_shop_and_status(
            db=db, shop_id=shop_id, status=status, skip=skip, limit=limit
        )
    else:
        orders = order_crud.get_by_shop(
            db=db, shop_id=shop_id, skip=skip, limit=limit
        )
    return orders

@router.post("/", response_model=Order)
def create_order(
    order_in: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    if order_in.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create order for another user",
        )
    
    order = order_crud.create_with_items(db=db, obj_in=order_in)
    
    cart_item_crud.clear_cart(db=db, user_id=current_user.id)
    
    return order

@router.get("/{order_id}", response_model=OrderWithItems)
def read_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    order = order_crud.get(db=db, id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.user_id != current_user.id:
        shop = order.shop
        if shop.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
    
    return order

@router.put("/{order_id}", response_model=Order)
def update_order(
    order_id: int,
    order_in: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_shop_admin),
) -> Any:
    order = order_crud.get(db=db, id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order = order_crud.update(db=db, db_obj=order, obj_in=order_in)
    return order

@router.put("/{order_id}/status", response_model=Order)
def update_order_status(
    order_id: int,
    status: OrderStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_shop_admin),
) -> Any:
    order = order_crud.get(db=db, id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order = order_crud.update_status(db=db, order_id=order_id, status=status)
    return order
