import pytest
from sqlalchemy.orm import Session

from backend.app.crud.user import user as user_crud, role as role_crud
from app.models.user import User, Role, UserRole
from app.schemas.user import UserCreate, UserUpdate

def test_create_user(db: Session):
    user_in = UserCreate(
        telegram_id="87654321",
        username="newuser",
        first_name="New",
        last_name="User",
        email="new@example.com"
    )
    user = user_crud.create(db=db, obj_in=user_in)
    
    assert user.telegram_id == "87654321"
    assert user.username == "newuser"
    assert user.is_active is True
    
def test_get_user(db: Session, test_user: User):
    user = user_crud.get(db=db, id=test_user.id)
    assert user
    assert user.telegram_id == test_user.telegram_id
    assert user.username == test_user.username

def test_get_user_by_telegram_id(db: Session, test_user: User):
    user = user_crud.get_by_telegram_id(db=db, telegram_id=test_user.telegram_id)
    assert user
    assert user.id == test_user.id
    assert user.username == test_user.username

def test_update_user(db: Session, test_user: User):
    user_update = UserUpdate(
        username="updateduser",
        email="updated@example.com"
    )
    updated_user = user_crud.update(db=db, db_obj=test_user, obj_in=user_update)
    
    assert updated_user.username == "updateduser"
    assert updated_user.email == "updated@example.com"
    assert updated_user.telegram_id == test_user.telegram_id

def test_add_role_to_user(db: Session, test_user: User, test_admin_role: Role, test_shop):
    user_role = user_crud.add_role_to_user(
        db=db, 
        user_id=test_user.id, 
        role_id=test_admin_role.id,
        shop_id=test_shop.id
    )
    
    assert user_role.user_id == test_user.id
    assert user_role.role_id == test_admin_role.id
    assert user_role.shop_id == test_shop.id

    user_roles = user_crud.get_user_roles(db=db, user_id=test_user.id, shop_id=test_shop.id)
    assert len(user_roles) == 1
    assert user_roles[0].role.name == "admin"

def test_remove_role_from_user(db: Session, test_user: User, test_admin_role: Role, test_shop):

    user_crud.add_role_to_user(
        db=db, 
        user_id=test_user.id, 
        role_id=test_admin_role.id,
        shop_id=test_shop.id
    )
    
    user_crud.remove_role_from_user(
        db=db,
        user_id=test_user.id,
        role_id=test_admin_role.id,
        shop_id=test_shop.id
    )
    
    user_roles = user_crud.get_user_roles(db=db, user_id=test_user.id, shop_id=test_shop.id)
    assert len(user_roles) == 0
