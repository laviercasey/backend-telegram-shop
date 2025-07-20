from typing import Any, Dict, List, Optional, Union
import httpx
import json
import logging
from sqlalchemy.orm import Session

from app.core.config import settings
from backend.app.crud.user import user as user_crud
from backend.app.crud.shop import shop as shop_crud
from app.schemas.user import UserCreate

logger = logging.getLogger(__name__)

class TelegramService:
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
    
    async def send_message(
        self,
        chat_id: Union[str, int],
        text: str,
        parse_mode: str = "HTML",
        reply_markup: Optional[Dict[str, Any]] = None,
        disable_web_page_preview: bool = False
    ) -> Dict[str, Any]:
        url = f"{self.api_url}/sendMessage"
        
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview
        }
        
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)
                result = response.json()
                
                if not result.get("ok"):
                    logger.error(f"Failed to send message: {result.get('description')}")
                
                return result
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return {"ok": False, "description": str(e)}
    
    async def send_photo(
        self,
        chat_id: Union[str, int],
        photo: str,
        caption: Optional[str] = None,
        parse_mode: str = "HTML",
        reply_markup: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        url = f"{self.api_url}/sendPhoto"
        
        payload = {
            "chat_id": chat_id,
            "photo": photo,
            "parse_mode": parse_mode
        }
        
        if caption:
            payload["caption"] = caption
        
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)
                result = response.json()
                
                if not result.get("ok"):
                    logger.error(f"Failed to send photo: {result.get('description')}")
                
                return result
        except Exception as e:
            logger.error(f"Error sending photo: {e}")
            return {"ok": False, "description": str(e)}
    
    async def set_webhook(self, url: str) -> Dict[str, Any]:
        webhook_url = f"{self.api_url}/setWebhook"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(webhook_url, params={"url": url})
                result = response.json()
                
                if not result.get("ok"):
                    logger.error(f"Failed to set webhook: {result.get('description')}")
                
                return result
        except Exception as e:
            logger.error(f"Error setting webhook: {e}")
            return {"ok": False, "description": str(e)}
    
    async def delete_webhook(self) -> Dict[str, Any]:
        url = f"{self.api_url}/deleteWebhook"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                return response.json()
        except Exception as e:
            logger.error(f"Error deleting webhook: {e}")
            return {"ok": False, "description": str(e)}
    
    async def get_webhook_info(self) -> Dict[str, Any]:
        url = f"{self.api_url}/getWebhookInfo"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                return response.json()
        except Exception as e:
            logger.error(f"Error getting webhook info: {e}")
            return {"ok": False, "description": str(e)}
    
    def create_web_app_button(self, text: str, url: str) -> Dict[str, Any]:
        return {
            "text": text,
            "web_app": {"url": url}
        }
    
    def create_inline_keyboard(self, buttons: List[List[Dict[str, Any]]]) -> Dict[str, Any]:
        return {"inline_keyboard": buttons}
    
    def create_keyboard(self, buttons: List[List[Dict[str, Any]]]) -> Dict[str, Any]:
        return {"keyboard": buttons, "resize_keyboard": True}


telegram_service = TelegramService(settings.TELEGRAM_BOT_TOKEN)


async def process_telegram_update(update: Dict[str, Any], db: Session) -> None:
    try:
        if "message" in update:
            await process_message(update["message"], db)
        elif "callback_query" in update:
            await process_callback_query(update["callback_query"], db)
        elif "my_chat_member" in update:
            await process_chat_member_update(update["my_chat_member"], db)
    except Exception as e:
        logger.error(f"Error processing Telegram update: {e}")


async def process_message(message: Dict[str, Any], db: Session) -> None:
    from_user = message.get("from")
    if not from_user:
        return
    
    chat_id = message.get("chat", {}).get("id")
    if not chat_id:
        return

    telegram_id = str(from_user.get("id"))
    user = user_crud.get_by_telegram_id(db=db, telegram_id=telegram_id)
    
    if not user:
        user_in = UserCreate(
            telegram_id=telegram_id,
            username=from_user.get("username"),
            first_name=from_user.get("first_name"),
            last_name=from_user.get("last_name")
        )
        user = user_crud.create(db=db, obj_in=user_in)
    
    text = message.get("text", "")
    
    if text.startswith("/start"):
        params = text.split(" ", 1)
        shop_id = None
        
        if len(params) > 1:
            try:
                shop_id = int(params[1])
            except ValueError:
                pass
        
        await handle_start_command(chat_id, user, shop_id, db)
    elif text.startswith("/help"):
        await handle_help_command(chat_id)
    elif text.startswith("/settings"):
        await handle_settings_command(chat_id, user)


async def process_callback_query(callback_query: Dict[str, Any], db: Session) -> None:
    query_id = callback_query.get("id")
    from_user = callback_query.get("from")
    message = callback_query.get("message")
    data = callback_query.get("data")
    
    if not query_id or not from_user or not message or not data:
        return
    
    chat_id = message.get("chat", {}).get("id")
    telegram_id = str(from_user.get("id"))
    
    user = user_crud.get_by_telegram_id(db=db, telegram_id=telegram_id)
    if not user:
        return
    
    if data.startswith("shop_"):
        shop_id = int(data.split("_")[1])
        await handle_shop_selection(chat_id, user, shop_id, db)


async def process_chat_member_update(chat_member: Dict[str, Any], db: Session) -> None:
    chat = chat_member.get("chat")
    new_chat_member = chat_member.get("new_chat_member")
    
    if not chat or not new_chat_member:
        return
    
    chat_id = chat.get("id")
    user = new_chat_member.get("user")
    status = new_chat_member.get("status")
    
    if not chat_id or not user or not status:
        return
    
    if status == "member" and user.get("id") == int(settings.TELEGRAM_BOT_TOKEN.split(":")[0]):
        await telegram_service.send_message(
            chat_id=chat_id,
            text="Спасибо за добавление меня в группу! Я работаю только в личных сообщениях. Пожалуйста, напишите мне в личку: @your_bot_username"
        )


async def handle_start_command(chat_id: int, user: Any, shop_id: Optional[int], db: Session) -> None:
    if shop_id:
        shop = shop_crud.get(db=db, id=shop_id)
        if shop:
            await show_shop(chat_id, user, shop)
        else:
            await telegram_service.send_message(
                chat_id=chat_id,
                text="Извините, указанный магазин не найден. Выберите другой магазин из списка ниже."
            )
            await show_shop_list(chat_id, db)
    else:
        welcome_message = (
            f"Здравствуйте, {user.first_name}! 👋\n\n"
            "Добро пожаловать в нашу платформу для покупок через Telegram.\n\n"
            "Вы можете выбрать магазин и начать покупки прямо сейчас!"
        )
        
        await telegram_service.send_message(
            chat_id=chat_id,
            text=welcome_message
        )
        
        await show_shop_list(chat_id, db)


async def handle_help_command(chat_id: int) -> None:
    help_text = (
        "📌 <b>Доступные команды:</b>\n\n"
        "/start - Начать покупки\n"
        "/help - Показать эту справку\n"
        "/settings - Настройки пользователя\n\n"
        "Для начала покупок, выберите магазин из списка или используйте команду /start."
    )
    
    await telegram_service.send_message(
        chat_id=chat_id,
        text=help_text
    )


async def handle_settings_command(chat_id: int, user: Any) -> None:
    settings_text = (
        f"⚙️ <b>Настройки пользователя</b>\n\n"
        f"Имя: {user.first_name} {user.last_name or ''}\n"
        f"Username: @{user.username or 'не указан'}\n"
        f"Email: {user.email or 'не указан'}\n"
        f"Телефон: {user.phone or 'не указан'}\n\n"
        "Для изменения настроек используйте кнопки ниже:"
    )
    
    settings_buttons = [
        [telegram_service.create_web_app_button(
            "✏️ Редактировать профиль", 
            f"{settings.FRONTEND_URL}/profile"
        )]
    ]
    
    keyboard = telegram_service.create_inline_keyboard(settings_buttons)
    
    await telegram_service.send_message(
        chat_id=chat_id,
        text=settings_text,
        reply_markup=keyboard
    )


async def show_shop_list(chat_id: int, db: Session) -> None:
    shops = shop_crud.get_multi(db=db, skip=0, limit=10)
    
    if not shops:
        await telegram_service.send_message(
            chat_id=chat_id,
            text="К сожалению, сейчас нет доступных магазинов. Пожалуйста, попробуйте позже."
        )
        return
    
    shop_list_text = "🏪 <b>Доступные магазины:</b>\n\nВыберите магазин для начала покупок:"
    
    shop_buttons = []
    for shop in shops:
        shop_buttons.append([{
            "text": shop.name,
            "callback_data": f"shop_{shop.id}"
        }])
    
    keyboard = telegram_service.create_inline_keyboard(shop_buttons)
    
    await telegram_service.send_message(
        chat_id=chat_id,
        text=shop_list_text,
        reply_markup=keyboard
    )


async def handle_shop_selection(chat_id: int, user: Any, shop_id: int, db: Session) -> None:
    shop = shop_crud.get(db=db, id=shop_id)
    if not shop:
        await telegram_service.send_message(
            chat_id=chat_id,
            text="Извините, выбранный магазин не найден. Пожалуйста, выберите другой магазин."
        )
        await show_shop_list(chat_id, db)
        return
    
    await show_shop(chat_id, user, shop)


async def show_shop(chat_id: int, user: Any, shop: Any) -> None:
    welcome_message = shop.welcome_message or f"Добро пожаловать в {shop.name}!"
    
    shop_info = (
        f"🏪 <b>{shop.name}</b>\n\n"
        f"{shop.description or ''}\n\n"
        f"{welcome_message}"
    )
    
    shop_buttons = [
        [telegram_service.create_web_app_button(
            "🛍️ Каталог товаров", 
            f"{settings.FRONTEND_URL}/shop/{shop.id}/catalog"
        )],
        [telegram_service.create_web_app_button(
            "🛒 Корзина", 
            f"{settings.FRONTEND_URL}/shop/{shop.id}/cart"
        )],
        [telegram_service.create_web_app_button(
            "📦 Мои заказы", 
            f"{settings.FRONTEND_URL}/shop/{shop.id}/orders"
        )]
    ]
    
    keyboard = telegram_service.create_inline_keyboard(shop_buttons)
    
    if shop.logo_url:
        await telegram_service.send_photo(
            chat_id=chat_id,
            photo=shop.logo_url,
            caption=shop_info,
            reply_markup=keyboard
        )
    else:
        await telegram_service.send_message(
            chat_id=chat_id,
            text=shop_info,
            reply_markup=keyboard
        )
