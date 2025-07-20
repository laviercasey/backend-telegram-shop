import pytest
import jwt
from datetime import datetime, timedelta

from app.core.security import (
    create_access_token,
    verify_telegram_auth,
    check_user_role
)
from app.core.config import settings

def test_create_access_token():
    subject = "test_subject"
    expires_delta = timedelta(minutes=30)
    
    token = create_access_token(subject=subject, expires_delta=expires_delta)

    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    
    assert payload["sub"] == subject
    expected_exp = datetime.utcnow() + expires_delta
    assert abs(payload["exp"] - expected_exp.timestamp()) < 1

def test_verify_telegram_auth_valid():
    with patch("hmac.new") as mock_hmac:
        mock_digest = mock_hmac.return_value
        mock_digest.hexdigest.return_value = "valid_hash"
        
        telegram_data = {
            "id": 12345678,
            "first_name": "Test",
            "username": "testuser",
            "auth_date": int(datetime.now().timestamp()),
            "hash": "valid_hash"
        }
        
        result = verify_telegram_auth(telegram_data)
        assert result is True

def test_verify_telegram_auth_invalid():
    telegram_data = {
        "id": 12345678,
        "first_name": "Test",
        "username": "testuser",
        "auth_date": int(datetime.now().timestamp()),
        "hash": "invalid_hash"
    }
    
    result = verify_telegram_auth(telegram_data)
    assert result is False

def test_check_user_role(db, test_user, test_admin_role, test_shop):
    from backend.app.crud.user import user as user_crud

    user_crud.add_role_to_user(
        db=db, 
        user_id=test_user.id, 
        role_id=test_admin_role.id,
        shop_id=test_shop.id
    )
    
    result = check_user_role(test_user, "admin", test_shop.id, db)
    assert result is True

    result = check_user_role(test_user, "manager", test_shop.id, db)
    assert result is False

    result = check_user_role(test_user, "admin", 999, db)
    assert result is False
