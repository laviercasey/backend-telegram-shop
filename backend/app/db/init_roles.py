from sqlalchemy.orm import Session

from backend.app.crud.user import role as role_crud
from app.models.user import Role

def init_roles(db: Session) -> None:
    roles = [
        {"name": "admin", "description": "Full access to shop administration"},
        {"name": "manager", "description": "Can manage products and orders"},
        {"name": "customer", "description": "Regular customer"}
    ]
    
    for role_data in roles:
        role = role_crud.get_by_name(db=db, name=role_data["name"])
        if not role:
            role = Role(**role_data)
            db.add(role)
    
    db.commit()
