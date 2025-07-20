import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from backend.app.db.session import SessionLocal
from backend.app.db.init_db import init_db

def init_database():
    db = SessionLocal()
    try:
        init_db(db)
        print("База данных успешно инициализирована!")
    except Exception as e:
        print(f"Ошибка при инициализации базы данных: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
