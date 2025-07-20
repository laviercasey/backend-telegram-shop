import pytest
from fastapi.testclient import TestClient

def test_read_shops(client, test_user, test_shop, user_token_headers):
    response = client.get(
        "/api/v1/shops/",
        headers=user_token_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["id"] == test_shop.id
    assert data[0]["name"] == test_shop.name
    assert data[0]["owner_id"] == test_user.id

def test_create_shop(client, test_user, user_token_headers):
    shop_data = {
        "name": "New API Test Shop",
        "description": "Shop created through API test",
        "welcome_message": "Welcome to API test shop!",
        "owner_id": test_user.id
    }
    
    response = client.post(
        "/api/v1/shops/",
        headers=user_token_headers,
        json=shop_data
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["name"] == shop_data["name"]
    assert data["description"] == shop_data["description"]
    assert data["owner_id"] == test_user.id
    assert data["is_active"] is True

    shop_id = data["id"]
    response = client.get(
        f"/api/v1/shops/{shop_id}",
        headers=user_token_headers
    )
    assert response.status_code == 200

def test_read_shop(client, test_shop, user_token_headers):
    response = client.get(
        f"/api/v1/shops/{test_shop.id}",
        headers=user_token_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == test_shop.id
    assert data["name"] == test_shop.name
    assert "settings" in data
    assert data["settings"]["shop_id"] == test_shop.id

def test_update_shop(client, test_shop, user_token_headers):
    shop_update = {
        "name": "Updated API Shop Name",
        "description": "Updated through API test"
    }
    
    response = client.put(
        f"/api/v1/shops/{test_shop.id}",
        headers=user_token_headers,
        json=shop_update
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == test_shop.id
    assert data["name"] == shop_update["name"]
    assert data["description"] == shop_update["description"]

def test_update_shop_settings(client, test_shop, user_token_headers):
    settings_update = {
        "currency": "EUR",
        "language": "fr"
    }
    
    response = client.put(
        f"/api/v1/shops/{test_shop.id}/settings",
        headers=user_token_headers,
        json=settings_update
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["shop_id"] == test_shop.id
    assert data["currency"] == "EUR"
    assert data["language"] == "fr"

def test_unauthorized_access(client, test_shop):
    response = client.get(f"/api/v1/shops/{test_shop.id}")
    assert response.status_code == 401
    
    response = client.put(
        f"/api/v1/shops/{test_shop.id}",
        json={"name": "Hacked Shop"}
    )
    assert response.status_code == 401
