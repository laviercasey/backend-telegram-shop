import pytest
from unittest.mock import patch
import json

def test_telegram_webhook_with_message(client, monkeypatch):
    with patch("app.api.v1.telegram.process_telegram_update") as mock_process:
        telegram_update = {
            "update_id": 123456789,
            "message": {
                "message_id": 123,
                "from": {
                    "id": 12345678,
                    "first_name": "Test",
                    "last_name": "User",
                    "username": "testuser"
                },
                "chat": {
                    "id": 12345678,
                    "type": "private"
                },
                "text": "/start"
            }
        }

        response = client.post(
            "/api/v1/telegram/webhook",
            json=telegram_update
        )
        
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        
        mock_process.assert_called_once()

def test_payment_webhook_stripe(client, test_order, monkeypatch):
    with patch("app.api.v1.payments.process_payment_callback") as mock_process:
        payment_data = {
            "id": "evt_123456",
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_123456",
                    "amount": test_order.total_amount * 100,
                    "status": "succeeded"
                }
            }
        }
        
        response = client.post(
            "/api/v1/payments/webhook/stripe",
            json=payment_data
        )
        
        assert response.status_code == 200
        assert response.json() == {"status": "processing"}
        
        mock_process.assert_called_once()
        args, kwargs = mock_process.call_args
        assert kwargs["provider"] == "stripe"
        assert kwargs["payload"] == payment_data
