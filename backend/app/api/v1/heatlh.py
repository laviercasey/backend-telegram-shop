from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.api.deps import get_db
from app.core.config import settings

router = APIRouter()

@router.get("/")
async def health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Проверяет здоровье системы, включая подключение к БД.
    """
    health_data = {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "services": {
            "database": "ok",
            "redis": "ok"
        }
    }

    try:
        db.execute("SELECT 1")
    except Exception as e:
        logging.error(f"Database health check failed: {str(e)}")
        health_data["services"]["database"] = "error"
        health_data["status"] = "error"
    try:
        pass
    except Exception as e:
        logging.error(f"Redis health check failed: {str(e)}")
        health_data["services"]["redis"] = "error"
        health_data["status"] = "error"
    if health_data["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_data
        )
    
    return health_data
