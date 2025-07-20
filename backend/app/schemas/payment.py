# app/schemas/payment.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.schemas.base import BaseSchema
from app.models.payment import PaymentStatus, PaymentProvider


class PaymentBase(BaseSchema):
    provider: PaymentProvider
    amount: float
    currency: str = "USD"
    details: Optional[str] = None


class PaymentCreate(PaymentBase):
    order_id: int
    provider_payment_id: Optional[str] = None


class PaymentUpdate(BaseSchema):
    provider_payment_id: Optional[str] = None
    status: Optional[PaymentStatus] = None
    details: Optional[str] = None


class Payment(PaymentBase):
    id: int
    order_id: int
    provider_payment_id: Optional[str] = None
    status: PaymentStatus
    created_at: datetime
    updated_at: datetime


class PaymentResponse(BaseSchema):
    success: bool
    payment_id: str
    provider_payment_id: Optional[str] = None
    status: PaymentStatus
    redirect_url: Optional[str] = None
    message: Optional[str] = None


class PaymentStatusResponse(BaseSchema):
    success: bool
    status: Optional[PaymentStatus] = None
    provider: Optional[PaymentProvider] = None
    provider_payment_id: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    message: Optional[str] = None


class RefundRequest(BaseSchema):
    amount: Optional[float] = None
    reason: Optional[str] = None


class RefundResponse(BaseSchema):
    success: bool
    refund_id: Optional[str] = None
    message: str


class PaymentHistoryItem(BaseSchema):
    id: int
    provider: PaymentProvider
    provider_payment_id: str
    amount: float
    currency: str
    status: PaymentStatus
    created_at: datetime
    is_refund: bool = False


class PaymentHistory(BaseSchema):
    payments: List[PaymentHistoryItem]
    total_count: int
