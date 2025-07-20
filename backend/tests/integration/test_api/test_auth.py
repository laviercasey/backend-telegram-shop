import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

def test_login_with_telegram_success(client, mock_telegram_auth_data):
    with patch("app.core.security.verify_telegram_auth", return_value=True):
        response = client.post(
            "/api/v1/auth/telegram-login",
            json=mock_telegram_auth_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "token" in data
        assert "user" in data
        assert "access_token" in data["token"]
        assert "token_type" in data["token"]
        assert data["token"]["token_type"] == "bearer"

        assert data["user"]["telegram_id"] == str(mock_telegram_auth_data["id"])
        assert data["user"]["username"] == mock_telegram_auth_data["username"]
        assert data["user"]["first_name"] == mock_telegram_auth_data["first_name"]
        assert data["user"]["last_name"] == mock_telegram_auth_data["last_name"]

def test_login_with_telegram_invalid_auth(client, mock_telegram_auth_data):
    with patch("app.core.security.verify_telegram_auth", return_value=False):
        response = client.post(
            "/api/v1/auth/telegram-login",
            json=mock_telegram_auth_data
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid authentication data" in data["detail"]

def test_get_access_token(client, test_user):
    response = client.post(
        f"/api/v1/auth/token?telegram_id={test_user.telegram_id}"
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"

def test_get_access_token_invalid_id(client):
    response = client.post(
        "/api/v1/auth/token?telegram_id=nonexistent_id"
    )
    
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert "Invalid telegram ID" in data["detail"]
