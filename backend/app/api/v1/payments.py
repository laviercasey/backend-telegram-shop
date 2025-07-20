from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user, get_shop_admin
from backend.app.crud.payment import payment as payment_crud
from backend.app.crud.order import order as order_crud
from app.services.payment_service import create_payment, process_payment_callback
from app.models.user import User
from app.models.payment import PaymentStatus, PaymentProvider
from app.models.order import OrderStatus
from app.schemas.payment import Payment, PaymentCreate, PaymentUpdate, PaymentResponse

router = APIRouter()

@router.post("/create/{order_id}", response_model=PaymentResponse)
async def create_payment_for_order(
    order_id: int,
    provider: PaymentProvider,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    order = order_crud.get(db=db, id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order is in {order.status} status, cannot create payment",
        )
    
    payment_result = await create_payment(
        order=order,
        provider=provider,
        db=db
    )
    
    return payment_result

@router.post("/webhook/{provider}")
async def payment_webhook(
    provider: PaymentProvider,
    payload: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Any:
    background_tasks.add_task(
        process_payment_callback,
        provider=provider,
        payload=payload,
        db=db
    )
    
    return {"status": "processing"}

@router.get("/{payment_id}", response_model=Payment)
async def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    payment = payment_crud.get(db=db, id=payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    order = order_crud.get(db=db, id=payment.order_id)
    if order.user_id != current_user.id:
        shop = order.shop
        if shop.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
    
    return payment

@router.put("/{payment_id}/status", response_model=Payment)
async def update_payment_status(
    payment_id: int,
    status: PaymentStatus,
    details: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_shop_admin),
) -> Any:
    payment = payment_crud.get(db=db, id=payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    payment = payment_crud.update_status(
        db=db, payment_id=payment_id, status=status, details=details
    )
    
    if status == PaymentStatus.COMPLETED:
        order_crud.update_status(
            db=db, order_id=payment.order_id, status=OrderStatus.PAID
        )
    elif status == PaymentStatus.FAILED:
        order_crud.update_status(
            db=db, order_id=payment.order_id, status=OrderStatus.PENDING
        )
    
    return payment
