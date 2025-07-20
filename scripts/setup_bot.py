import asyncio
import argparse
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.services.telegram_service import telegram_service
from backend.app.core.config import settings


async def setup_telegram_bot(webhook_url=None, delete_webhook=False):
    if delete_webhook:
        print("Удаление текущего вебхука...")
        result = await telegram_service.delete_webhook()
        print(f"Результат: {result}")
        return
    
    webhook_info = await telegram_service.get_webhook_info()
    print(f"Текущая информация о вебхуке: {webhook_info}")
    
    if webhook_url:
        print(f"Установка нового вебхука: {webhook_url}")
        result = await telegram_service.set_webhook(webhook_url)
        print(f"Результат: {result}")
    elif settings.TELEGRAM_WEBHOOK_URL:
        print(f"Установка вебхука из настроек: {settings.TELEGRAM_WEBHOOK_URL}")
        result = await telegram_service.set_webhook(settings.TELEGRAM_WEBHOOK_URL)
        print(f"Результат: {result}")
    else:
        print("URL вебхука не указан ни в аргументах, ни в настройках.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Настройка Telegram бота")
    parser.add_argument("--webhook-url", help="URL для вебхука Telegram бота")
    parser.add_argument("--delete-webhook", action="store_true", help="Удалить текущий вебхук")
    
    args = parser.parse_args()
    
    asyncio.run(setup_telegram_bot(args.webhook_url, args.delete_webhook))
