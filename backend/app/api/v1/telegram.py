from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request, Body
from sqlalchemy.orm import Session
import json

from app.api.deps import get_db, get_shop_owner
from app.core.config import settings
from app.services.telegram_service import telegram_service, process_telegram_update
from backend.app.crud.shop import shop as shop_crud
from app.models.user import User

router = APIRouter()

@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Any:
    if settings.TELEGRAM_WEBHOOK_SECRET:
        secret_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if not secret_header or secret_header != settings.TELEGRAM_WEBHOOK_SECRET:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid secret token"
            )
    
    update = await request.json()
    
    if settings.DEBUG:
        import logging
        logging.debug(f"Received Telegram update: {json.dumps(update, indent=2)}")
    
    background_tasks.add_task(
        process_telegram_update,
        update=update,
        db=db
    )
    
    return {"status": "ok"}

@router.post("/send-message/{shop_id}")
async def send_message_to_user(
    shop_id: int,
    telegram_id: str,
    message: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_shop_owner),
) -> Any:
    shop = shop_crud.get(db=db, id=shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    result = await telegram_service.send_message(
        chat_id=telegram_id,
        text=message
    )
    
    return result

@router.post("/broadcast/{shop_id}")
async def broadcast_message(
    shop_id: int,
    message: str,
    user_ids: Optional[list] = Body(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_shop_owner),
) -> Any:
    shop = shop_crud.get(db=db, id=shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    if not user_ids:
        return {"status": "error", "message": "No users specified"}
    
    results = []
    for telegram_id in user_ids:
        result = await telegram_service.send_message(
            chat_id=telegram_id,
            text=message
        )
        results.append({"telegram_id": telegram_id, "result": result})
    
    return {"status": "ok", "results": results}

@router.post("/set-webhook")
async def set_telegram_webhook(
    secret_token: Optional[str] = None
) -> Any:
    webhook_url = settings.TELEGRAM_WEBHOOK_URL
    if not webhook_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook URL not configured in settings"
        )
    
    if secret_token:
        settings.TELEGRAM_WEBHOOK_SECRET = secret_token
    
    result = await telegram_service.set_webhook(webhook_url)
    
    if not result.get("ok"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set webhook: {result.get('description')}"
        )
    
    return result

@router.get("/webhook-info")
async def get_webhook_info() -> Any:
    result = await telegram_service.get_webhook_info()
    
    if not result.get("ok"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get webhook info: {result.get('description')}"
        )
    
    return result

@router.post("/delete-webhook")
async def delete_telegram_webhook() -> Any:
    result = await telegram_service.delete_webhook()
    
    if not result.get("ok"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete webhook: {result.get('description')}"
        )
    
    return result

@router.post("/shop/{shop_id}/welcome-message")
async def update_shop_welcome_message(
    shop_id: int,
    welcome_message: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_shop_owner),
) -> Any:
    shop = shop_crud.get(db=db, id=shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    shop = shop_crud.update(
        db=db, 
        db_obj=shop, 
        obj_in={"welcome_message": welcome_message}
    )
    
    return {"status": "success", "shop": shop}
