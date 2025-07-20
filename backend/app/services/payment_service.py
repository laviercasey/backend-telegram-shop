from typing import Any, Dict, Optional, List, Tuple
import json
import hmac
import hashlib
import uuid
import httpx
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.payment import PaymentProvider, PaymentStatus
from app.models.order import Order, OrderStatus
from app.schemas.payment import PaymentCreate, PaymentUpdate
from backend.app.crud.payment import payment as payment_crud
from backend.app.crud.order import order as order_crud

logger = logging.getLogger(__name__)

class StripePaymentService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.stripe.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
    
    async def create_payment(self, order: Order, return_url: str) -> Dict[str, Any]:
        """Создает платеж в Stripe"""
        try:
            payload = {
                "amount": int(order.total_amount * 100),
                "currency": order.shop.settings.currency.lower(),
                "payment_method_types[]": "card",
                "description": f"Заказ {order.order_number} в магазине {order.shop.name}",
                "metadata[order_id]": str(order.id),
                "metadata[order_number]": order.order_number,
                "success_url": f"{return_url}/success?session_id={{CHECKOUT_SESSION_ID}}",
                "cancel_url": f"{return_url}/cancel?session_id={{CHECKOUT_SESSION_ID}}"
            }
            
            for i, item in enumerate(order.items):
                payload[f"line_items[{i}][price_data][currency]"] = order.shop.settings.currency.lower()
                payload[f"line_items[{i}][price_data][unit_amount]"] = int(item.price * 100)
                payload[f"line_items[{i}][price_data][product_data][name]"] = item.product.name
                payload[f"line_items[{i}][quantity]"] = item.quantity
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/checkout/sessions",
                    headers=self.headers,
                    data=payload
                )
                
                if response.status_code != 200:
                    logger.error(f"Stripe error: {response.text}")
                    return {
                        "id": None,
                        "url": None,
                        "status": "error",
                        "error": response.text
                    }
                
                data = response.json()
                return {
                    "id": data["id"],
                    "url": data["url"],
                    "status": data["status"],
                    "provider_data": data
                }
        
        except Exception as e:
            logger.error(f"Error creating Stripe payment: {str(e)}")
            return {
                "id": None,
                "url": None,
                "status": "error",
                "error": str(e)
            }
    
    async def verify_webhook(self, payload: bytes, signature: str) -> bool:
        """Проверяет подпись вебхука от Stripe"""
        try:
            webhook_secret = settings.PAYMENT_PROVIDERS.get("stripe", {}).get("webhook_secret")
            if not webhook_secret:
                logger.warning("Stripe webhook secret not configured")
                return False
            
            expected_sig = hmac.new(
                webhook_secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_sig, signature)
        
        except Exception as e:
            logger.error(f"Error verifying Stripe webhook: {str(e)}")
            return False
    
    async def process_webhook(self, payload: Dict[str, Any]) -> Tuple[bool, str, Optional[str]]:
        """Обрабатывает вебхук от Stripe"""
        try:
            event_type = payload.get("type")
            
            if event_type == "checkout.session.completed":
                session = payload.get("data", {}).get("object", {})
                payment_id = session.get("id")
                payment_status = session.get("payment_status")
                order_id = session.get("metadata", {}).get("order_id")
                
                if payment_status == "paid":
                    return True, PaymentStatus.COMPLETED, order_id
                else:
                    return True, PaymentStatus.PENDING, order_id
            
            elif event_type == "checkout.session.expired":
                session = payload.get("data", {}).get("object", {})
                payment_id = session.get("id")
                order_id = session.get("metadata", {}).get("order_id")
                
                return True, PaymentStatus.FAILED, order_id
            
            elif event_type == "charge.refunded":
                charge = payload.get("data", {}).get("object", {})
                payment_id = charge.get("payment_intent")
                order_id = charge.get("metadata", {}).get("order_id")
                
                return True, PaymentStatus.REFUNDED, order_id
            
            return False, None, None
        
        except Exception as e:
            logger.error(f"Error processing Stripe webhook: {str(e)}")
            return False, None, None
    
    async def refund_payment(self, payment_id: str, amount: Optional[float] = None) -> Dict[str, Any]:
        """Возвращает средства по платежу"""
        try:
            payload = {"payment_intent": payment_id}
            if amount:
                payload["amount"] = int(amount * 100)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/refunds",
                    headers=self.headers,
                    data=payload
                )
                
                if response.status_code != 200:
                    logger.error(f"Stripe refund error: {response.text}")
                    return {
                        "success": False,
                        "error": response.text
                    }
                
                data = response.json()
                return {
                    "success": True,
                    "refund_id": data["id"],
                    "status": data["status"],
                    "provider_data": data
                }
        
        except Exception as e:
            logger.error(f"Error refunding Stripe payment: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


class PayPalPaymentService:
    def __init__(self, client_id: str, client_secret: str, sandbox: bool = True):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://api-m.sandbox.paypal.com" if sandbox else "https://api-m.paypal.com"
        self.sandbox = sandbox
    
    async def _get_access_token(self) -> Optional[str]:
        """Получает access token от PayPal"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/v1/oauth2/token",
                    auth=(self.client_id, self.client_secret),
                    data={"grant_type": "client_credentials"}
                )
                
                if response.status_code != 200:
                    logger.error(f"PayPal auth error: {response.text}")
                    return None
                
                data = response.json()
                return data.get("access_token")
        
        except Exception as e:
            logger.error(f"Error getting PayPal access token: {str(e)}")
            return None
    
    async def create_payment(self, order: Order, return_url: str) -> Dict[str, Any]:
        """Создает платеж в PayPal"""
        try:
            access_token = await self._get_access_token()
            if not access_token:
                return {
                    "id": None,
                    "url": None,
                    "status": "error",
                    "error": "Failed to get PayPal access token"
                }
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "intent": "CAPTURE",
                "purchase_units": [
                    {
                        "reference_id": order.order_number,
                        "description": f"Заказ в магазине {order.shop.name}",
                        "custom_id": str(order.id),
                        "amount": {
                            "currency_code": order.shop.settings.currency,
                            "value": str(order.total_amount),
                            "breakdown": {
                                "item_total": {
                                    "currency_code": order.shop.settings.currency,
                                    "value": str(order.total_amount - (order.shipping_cost or 0))
                                }
                            }
                        },
                        "items": [
                            {
                                "name": item.product.name,
                                "quantity": str(item.quantity),
                                "unit_amount": {
                                    "currency_code": order.shop.settings.currency,
                                    "value": str(item.price)
                                }
                            } for item in order.items
                        ]
                    }
                ],
                "application_context": {
                    "return_url": f"{return_url}/success",
                    "cancel_url": f"{return_url}/cancel"
                }
            }
            
            if order.shipping_cost:
                payload["purchase_units"][0]["amount"]["breakdown"]["shipping"] = {
                    "currency_code": order.shop.settings.currency,
                    "value": str(order.shipping_cost)
                }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/v2/checkout/orders",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code not in (200, 201):
                    logger.error(f"PayPal error: {response.text}")
                    return {
                        "id": None,
                        "url": None,
                        "status": "error",
                        "error": response.text
                    }
                
                data = response.json()
                
                approval_url = next(
                    (link["href"] for link in data.get("links", []) 
                     if link["rel"] == "approve"),
                    None
                )
                
                return {
                    "id": data["id"],
                    "url": approval_url,
                    "status": data["status"],
                    "provider_data": data
                }
        
        except Exception as e:
            logger.error(f"Error creating PayPal payment: {str(e)}")
            return {
                "id": None,
                "url": None,
                "status": "error",
                "error": str(e)
            }
    
    async def verify_webhook(self, payload: bytes, headers: Dict[str, str]) -> bool:
        """Проверяет подпись вебхука от PayPal"""
        try:
            webhook_id = settings.PAYMENT_PROVIDERS.get("paypal", {}).get("webhook_id")
            if not webhook_id:
                logger.warning("PayPal webhook ID not configured")
                return False
            
            access_token = await self._get_access_token()
            if not access_token:
                return False
            
            verify_data = {
                "webhook_id": webhook_id,
                "auth_algo": headers.get("PAYPAL-AUTH-ALGO"),
                "cert_url": headers.get("PAYPAL-CERT-URL"),
                "transmission_id": headers.get("PAYPAL-TRANSMISSION-ID"),
                "transmission_sig": headers.get("PAYPAL-TRANSMISSION-SIG"),
                "transmission_time": headers.get("PAYPAL-TRANSMISSION-TIME"),
                "webhook_event": json.loads(payload)
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/v1/notifications/verify-webhook-signature",
                    headers={"Authorization": f"Bearer {access_token}"},
                    json=verify_data
                )
                
                if response.status_code != 200:
                    logger.error(f"PayPal webhook verification error: {response.text}")
                    return False
                
                data = response.json()
                return data.get("verification_status") == "SUCCESS"
        
        except Exception as e:
            logger.error(f"Error verifying PayPal webhook: {str(e)}")
            return False
    
    async def process_webhook(self, payload: Dict[str, Any]) -> Tuple[bool, str, Optional[str]]:
        """Обрабатывает вебхук от PayPal"""
        try:
            event_type = payload.get("event_type")
            resource = payload.get("resource", {})
            
            if event_type == "PAYMENT.CAPTURE.COMPLETED":
                payment_id = resource.get("id")
                custom_id = resource.get("custom_id")
                
                return True, PaymentStatus.COMPLETED, custom_id
            
            elif event_type == "PAYMENT.CAPTURE.DENIED":
                payment_id = resource.get("id")
                custom_id = resource.get("custom_id")
                
                return True, PaymentStatus.FAILED, custom_id
            
            elif event_type == "PAYMENT.CAPTURE.REFUNDED":
                payment_id = resource.get("id")
                custom_id = resource.get("custom_id")
                
                return True, PaymentStatus.REFUNDED, custom_id
            
            return False, None, None
        
        except Exception as e:
            logger.error(f"Error processing PayPal webhook: {str(e)}")
            return False, None, None
    
    async def refund_payment(self, payment_id: str, amount: Optional[float] = None) -> Dict[str, Any]:
        """Возвращает средства по платежу"""
        try:
            access_token = await self._get_access_token()
            if not access_token:
                return {
                    "success": False,
                    "error": "Failed to get PayPal access token"
                }
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {}
            if amount:
                payload["amount"] = {
                    "value": str(amount),
                    "currency_code": "USD"
                }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/v2/payments/captures/{payment_id}/refund",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code not in (200, 201):
                    logger.error(f"PayPal refund error: {response.text}")
                    return {
                        "success": False,
                        "error": response.text
                    }
                
                data = response.json()
                return {
                    "success": True,
                    "refund_id": data["id"],
                    "status": data["status"],
                    "provider_data": data
                }
        
        except Exception as e:
            logger.error(f"Error refunding PayPal payment: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


class YooKassaPaymentService:
    def __init__(self, shop_id: str, secret_key: str):
        self.shop_id = shop_id
        self.secret_key = secret_key
        self.base_url = "https://api.yookassa.ru/v3"
        self.headers = {
            "Content-Type": "application/json",
            "Idempotence-Key": ""
        }
    
    async def create_payment(self, order: Order, return_url: str) -> Dict[str, Any]:
        """Создает платеж в ЮKassa"""
        try:
            idempotence_key = str(uuid.uuid4())
            headers = self.headers.copy()
            headers["Idempotence-Key"] = idempotence_key
            
            auth = (self.shop_id, self.secret_key)
            
            payload = {
                "amount": {
                    "value": str(order.total_amount),
                    "currency": order.shop.settings.currency
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": return_url
                },
                "capture": True,
                "description": f"Заказ {order.order_number} в магазине {order.shop.name}",
                "metadata": {
                    "order_id": str(order.id),
                    "order_number": order.order_number
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/payments",
                    headers=headers,
                    json=payload,
                    auth=auth
                )
                
                if response.status_code not in (200, 201):
                    logger.error(f"YooKassa error: {response.text}")
                    return {
                        "id": None,
                        "url": None,
                        "status": "error",
                        "error": response.text
                    }
                
                data = response.json()
                confirmation_url = data.get("confirmation", {}).get("confirmation_url")
                
                return {
                    "id": data["id"],
                    "url": confirmation_url,
                    "status": data["status"],
                    "provider_data": data
                }
        
        except Exception as e:
            logger.error(f"Error creating YooKassa payment: {str(e)}")
            return {
                "id": None,
                "url": None,
                "status": "error",
                "error": str(e)
            }
    
    async def verify_webhook(self, payload: bytes, headers: Dict[str, str]) -> bool:
        """Проверяет подпись вебхука от ЮKassa"""
        return True
    
    async def process_webhook(self, payload: Dict[str, Any]) -> Tuple[bool, str, Optional[str]]:
        """Обрабатывает вебхук от ЮKassa"""
        try:
            event = payload.get("event")
            payment = payload.get("object", {})
            
            if not event or not payment:
                return False, None, None
            
            payment_id = payment.get("id")
            order_id = payment.get("metadata", {}).get("order_id")
            
            if event == "payment.succeeded":
                return True, PaymentStatus.COMPLETED, order_id
            
            elif event == "payment.canceled":
                return True, PaymentStatus.FAILED, order_id
            
            elif event == "refund.succeeded":
                return True, PaymentStatus.REFUNDED, order_id
            
            return False, None, None
        
        except Exception as e:
            logger.error(f"Error processing YooKassa webhook: {str(e)}")
            return False, None, None
    
    async def refund_payment(self, payment_id: str, amount: Optional[float] = None) -> Dict[str, Any]:
        """Возвращает средства по платежу"""
        try:
            idempotence_key = str(uuid.uuid4())
            headers = self.headers.copy()
            headers["Idempotence-Key"] = idempotence_key
            
            auth = (self.shop_id, self.secret_key)
            
            payload = {
                "payment_id": payment_id
            }
            
            if amount:
                payload["amount"] = {
                    "value": str(amount),
                    "currency": "RUB"
                }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/refunds",
                    headers=headers,
                    json=payload,
                    auth=auth
                )
                
                if response.status_code not in (200, 201):
                    logger.error(f"YooKassa refund error: {response.text}")
                    return {
                        "success": False,
                        "error": response.text
                    }
                
                data = response.json()
                return {
                    "success": True,
                    "refund_id": data["id"],
                    "status": data["status"],
                    "provider_data": data
                }
        
        except Exception as e:
            logger.error(f"Error refunding YooKassa payment: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

def get_payment_service(provider: PaymentProvider) -> Any:
    """Возвращает экземпляр сервиса для указанного провайдера"""
    if provider == PaymentProvider.STRIPE:
        api_key = settings.PAYMENT_PROVIDERS.get("stripe", {}).get("api_key", "")
        return StripePaymentService(api_key)
    
    elif provider == PaymentProvider.PAYPAL:
        client_id = settings.PAYMENT_PROVIDERS.get("paypal", {}).get("client_id", "")
        client_secret = settings.PAYMENT_PROVIDERS.get("paypal", {}).get("secret", "")
        sandbox = settings.PAYMENT_PROVIDERS.get("paypal", {}).get("sandbox", True)
        return PayPalPaymentService(client_id, client_secret, sandbox)
    
    elif provider == PaymentProvider.YOOKASSA:
        shop_id = settings.PAYMENT_PROVIDERS.get("yookassa", {}).get("shop_id", "")
        secret_key = settings.PAYMENT_PROVIDERS.get("yookassa", {}).get("secret_key", "")
        return YooKassaPaymentService(shop_id, secret_key)
    
    return None


async def create_payment(
    order: Order,
    provider: PaymentProvider,
    db: Session
) -> Dict[str, Any]:
    shop_settings = order.shop.settings
    payment_providers = shop_settings.payment_providers
    if isinstance(payment_providers, str):
        payment_providers = json.loads(payment_providers)
    
    if not payment_providers.get(provider.value, False):
        return {
            "success": False,
            "payment_id": "",
            "status": PaymentStatus.FAILED,
            "message": f"Payment provider {provider.value} is not enabled for this shop"
        }
    
    service = get_payment_service(provider)
    if not service:
        return {
            "success": False,
            "payment_id": "",
            "status": PaymentStatus.FAILED,
            "message": f"Payment provider {provider.value} is not configured properly"
        }
    
    return_url = f"{settings.FRONTEND_URL}/shop/{order.shop_id}/orders/{order.id}/payment"
    
    result = await service.create_payment(order, return_url)
    
    if not result.get("id"):
        return {
            "success": False,
            "payment_id": "",
            "status": PaymentStatus.FAILED,
            "message": f"Failed to create payment: {result.get('error')}"
        }
    
    payment_in = PaymentCreate(
        order_id=order.id,
        provider=provider,
        provider_payment_id=result["id"],
        amount=order.total_amount,
        currency=shop_settings.currency,
        details=json.dumps(result.get("provider_data", {}))
    )
    
    payment = payment_crud.create(db=db, obj_in=payment_in)
    
    return {
        "success": True,
        "payment_id": str(payment.id),
        "provider_payment_id": result["id"],
        "status": PaymentStatus.PENDING,
        "redirect_url": result["url"],
        "message": "Payment created successfully"
    }


async def process_payment_callback(
    provider: PaymentProvider,
    payload: Dict[str, Any],
    headers: Dict[str, str],
    raw_payload: bytes,
    db: Session
) -> bool:
    service = get_payment_service(provider)
    if not service:
        logger.error(f"Payment provider {provider.value} is not configured")
        return False
    
    is_valid = await service.verify_webhook(raw_payload, headers)
    if not is_valid:
        logger.error(f"Invalid webhook signature for {provider.value}")
        return False
    
    success, status, order_id = await service.process_webhook(payload)
    if not success or not status or not order_id:
        logger.error(f"Failed to process webhook for {provider.value}")
        return False
    
    try:
        order = order_crud.get(db=db, id=int(order_id))
        if not order:
            logger.error(f"Order {order_id} not found")
            return False
        
        payment = payment_crud.get_by_order(db=db, order_id=order.id)
        if not payment:
            logger.error(f"Payment for order {order_id} not found")
            return False
        
        payment = payment_crud.update_status(
            db=db, 
            payment_id=payment.id, 
            status=status,
            details=json.dumps(payload)
        )
        
        if status == PaymentStatus.COMPLETED:
            order_crud.update_status(
                db=db, 
                order_id=order.id, 
                status=OrderStatus.PAID
            )
        elif status == PaymentStatus.FAILED:
            order_crud.update_status(
                db=db, 
                order_id=order.id, 
                status=OrderStatus.PENDING
            )
        elif status == PaymentStatus.REFUNDED:
            order_crud.update_status(
                db=db, 
                order_id=order.id, 
                status=OrderStatus.REFUNDED
            )
        
        return True
    
    except Exception as e:
        logger.error(f"Error processing payment callback: {str(e)}")
        return False


async def refund_payment(
    payment_id: int,
    amount: Optional[float] = None,
    db: Session
) -> Dict[str, Any]:
    payment = payment_crud.get(db=db, id=payment_id)
    if not payment:
        return {
            "success": False,
            "message": "Payment not found"
        }
    
    if payment.status != PaymentStatus.COMPLETED:
        return {
            "success": False,
            "message": f"Cannot refund payment with status {payment.status}"
        }
    
    service = get_payment_service(payment.provider)
    if not service:
        return {
            "success": False,
            "message": f"Payment provider {payment.provider.value} is not configured"
        }
    
    result = await service.refund_payment(payment.provider_payment_id, amount)
    
    if not result.get("success"):
        return {
            "success": False,
            "message": f"Failed to refund payment: {result.get('error')}"
        }
    payment = payment_crud.update_status(
        db=db, 
        payment_id=payment.id, 
        status=PaymentStatus.REFUNDED,
        details=json.dumps(result.get("provider_data", {}))
    )
    
    order = order_crud.get(db=db, id=payment.order_id)
    if order:
        order_crud.update_status(
            db=db, 
            order_id=order.id, 
            status=OrderStatus.REFUNDED
        )
    
    return {
        "success": True,
        "refund_id": result.get("refund_id"),
        "message": "Payment refunded successfully"
    }


async def get_payment_status(
    payment_id: int,
    db: Session
) -> Dict[str, Any]:
    payment = payment_crud.get(db=db, id=payment_id)
    if not payment:
        return {
            "success": False,
            "message": "Payment not found"
        }
    
    return {
        "success": True,
        "status": payment.status,
        "provider": payment.provider,
        "provider_payment_id": payment.provider_payment_id,
        "amount": payment.amount,
        "currency": payment.currency,
        "created_at": payment.created_at.isoformat(),
        "updated_at": payment.updated_at.isoformat()
    }
