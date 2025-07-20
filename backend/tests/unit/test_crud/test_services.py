import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json

from app.services.telegram_service import (
    telegram_service, 
    process_message, 
    handle_start_command,
    show_shop_list
)
from app.schemas.user import UserCreate

@pytest.fixture
def mock_httpx_client():
    with patch("httpx.AsyncClient") as mock:
        client_instance = AsyncMock()
        mock.return_value.__aenter__.return_value = client_instance
        
        response = MagicMock()
        response.json.return_value = {"ok": True, "result": {"message_id": 123}}
        client_instance.post.return_value = response
        client_instance.get.return_value = response
        
        yield client_instance

@pytest.mark.asyncio
async def test_send_message(mock_httpx_client):
    result = await telegram_service.send_message(
        chat_id="12345",
        text="Test message"
    )
    
    mock_httpx_client.post.assert_called_once()
    
    args, kwargs = mock_httpx_client.post.call_args
    assert f"{telegram_service.api_url}/sendMessage" in args[0]
    assert kwargs["json"]["chat_id"] == "12345"
    assert kwargs["json"]["text"] == "Test message"
    
    assert result["ok"] is True
    assert result["result"]["message_id"] == 123

@pytest.mark.asyncio
async def test_set_webhook(mock_httpx_client):
    result = await telegram_service.set_webhook("https://example.com/webhook")
    
    mock_httpx_client.post.assert_called_once()
    
    args, kwargs = mock_httpx_client.post.call_args
    assert f"{telegram_service.api_url}/setWebhook" in args[0]
    assert kwargs["params"]["url"] == "https://example.com/webhook"

    assert result["ok"] is True

@pytest.mark.asyncio
async def test_process_message(db, test_user):
    message = {
        "message_id": 123,
        "from": {
            "id": int(test_user.telegram_id),
            "first_name": test_user.first_name,
            "last_name": test_user.last_name,
            "username": test_user.username
        },
        "chat": {
            "id": int(test_user.telegram_id),
            "type": "private"
        },
        "text": "/start"
    }
    
    with patch("app.services.telegram_service.handle_start_command") as mock_handle:
        mock_handle.return_value = None
        
        await process_message(message, db)
        
        mock_handle.assert_called_once()
        
        args, kwargs = mock_handle.call_args
        assert args[0] == int(test_user.telegram_id)
        assert args[1].id == test_user.id 
        assert args[2] is None  
        assert args[3] == db

@pytest.mark.asyncio
async def test_handle_start_command_with_shop_id(db, test_user, test_shop):
    with patch("app.services.telegram_service.show_shop") as mock_show_shop:
        mock_show_shop.return_value = None

        await handle_start_command(
            chat_id=int(test_user.telegram_id),
            user=test_user,
            shop_id=test_shop.id,
            db=db
        )
        
        mock_show_shop.assert_called_once()

        args, kwargs = mock_show_shop.call_args
        assert args[0] == int(test_user.telegram_id)
        assert args[1].id == test_user.id
        assert args[2].id == test_shop.id

@pytest.mark.asyncio
async def test_show_shop_list(db, test_user, test_shop):
    with patch.object(telegram_service, "send_message") as mock_send:
        mock_send.return_value = {"ok": True}
        
        await show_shop_list(int(test_user.telegram_id), db)

        mock_send.assert_called_once()
        
        args, kwargs = mock_send.call_args
        assert kwargs["chat_id"] == int(test_user.telegram_id)
        assert "Доступные магазины" in kwargs["text"]
        assert "reply_markup" in kwargs
        
        keyboard = json.loads(kwargs["reply_markup"])
        assert "inline_keyboard" in keyboard
        assert len(keyboard["inline_keyboard"]) >= 1
        assert test_shop.name in keyboard["inline_keyboard"][0][0]["text"]
