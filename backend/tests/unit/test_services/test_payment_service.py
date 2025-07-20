import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json

from app.services.payment_service import (
    create_payment,
    process_payment_callback,
    create_stripe_payment,
    create_paypal_payment,
    create_yookassa_payment
)
from app.models.payment import PaymentProvider, PaymentStatus
from app.models.order import OrderStatus

@pytest.mark.asyncio
async def test_create_stripe_payment(test_order):
    result = await create_stripe_payment(test_order)
    
    assert "id" in result
    assert "url" in result
    assert f"stripe_payment_{test_order.id}" == result["id"]
    assert f"https://stripe.com/pay/{test_order.id}" == result["url"]

@pytest.mark.asyncio
async def test_create_payment(db, test_order, test_shop, monkeypatch):
    async def mock_create_stripe(*args, **kwargs):
        return {
            "id": f"stripe_payment_{test_order.id}",
            "url": f"https://stripe.com/pay/{test_order.id}"
        }
    
    monkeypatch.setattr("app.services.payment_service.create_stripe_payment", mock_create_stripe)

    test_shop.settings.payment_providers = json.dumps({"stripe": True, "paypal": False, "yookassa": False})
    db.add(test_shop.settings)
    db.commit()
    
    result = await create_payment(
        order=test_order,
        provider=PaymentProvider.STRIPE,
        db=db
    )
    
    assert result["success"] is True
    assert "payment_id" in result
    assert result["provider_payment_id"] == f"stripe_payment_{test_order.id}"
    assert result["status"] == PaymentStatus.PENDING
    assert result["redirect_url"] == f"https://stripe.com/pay/{test_order.id}"

@pytest.mark.asyncio
async def test_create_payment_provider_disabled(db, test_order, test_shop):
    test_shop.settings.payment_providers = json.dumps({"stripe": False, "paypal": False, "yookassa": False})
    db.add(test_shop.settings)
    db.commit()
    
    result = await create_payment(
        order=test_order,
        provider=PaymentProvider.STRIPE,
        db=db
    )
 
    assert result["success"] is False
    assert result["status"] == PaymentStatus.FAILED
    assert "not enabled" in result["message"]

@pytest.mark.asyncio
async def test_process_payment_callback_success(db, test_order, monkeypatch):
    from app.schemas.payment import PaymentCreate
    from backend.app.crud.payment import payment as payment_crud
    
    payment_in = PaymentCreate(
        order_id=test_order.id,
        provider=PaymentProvider.STRIPE,
        provider_payment_id="stripe_payment_123",
        amount=test_order.total_amount,
        currency="USD"
    )
    payment = payment_crud.create(db=db, obj_in=payment_in)
  
    payload = {
        "id": "stripe_payment_123",
        "status": "succeeded",
        "amount": test_order.total_amount * 100,
        "currency": "usd"
    }

    await process_payment_callback(
        provider=PaymentProvider.STRIPE,
        payload=payload,
        db=db
    )
    
    db.refresh(payment)
    assert payment.status == PaymentStatus.COMPLETED
    
    db.refresh(test_order)
    assert test_order.status == OrderStatus.PAID
