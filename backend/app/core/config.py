from pydantic_settings import BaseSettings
from typing import List, Optional, Dict, Any, Union


class PaymentProviderSettings(BaseSettings):
    enabled: bool = False
    api_key: str = ""
    webhook_secret: Optional[str] = None


class StripeSettings(PaymentProviderSettings):
    pass


class PayPalSettings(PaymentProviderSettings):
    client_id: str = ""
    secret: str = ""
    sandbox: bool = True
    webhook_id: Optional[str] = None


class YooKassaSettings(PaymentProviderSettings):
    shop_id: str = ""
    secret_key: str = ""


class StorageSettings(BaseSettings):
    type: str = "local"
    local_path: str = "./uploads"
    s3_bucket: Optional[str] = None
    s3_region: Optional[str] = None
    s3_access_key: Optional[str] = None
    s3_secret_key: Optional[str] = None


class Settings(BaseSettings):
    PROJECT_NAME: str = "Telegram Shop API"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "YOUR_SECRET_KEY_HERE"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "telegram_shop"
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    TELEGRAM_BOT_TOKEN: str = "YOUR_BOT_TOKEN"
    TELEGRAM_WEBHOOK_URL: Optional[str] = None
    TELEGRAM_WEBHOOK_SECRET: Optional[str] = None
    
    STRIPE: StripeSettings = StripeSettings()
    PAYPAL: PayPalSettings = PayPalSettings()
    YOOKASSA: YooKassaSettings = YooKassaSettings()
    
    PAYMENT_PROVIDERS: Dict[str, Dict[str, Any]] = {
        "stripe": {"enabled": False, "api_key": ""},
        "paypal": {"enabled": False, "client_id": "", "secret": ""},
        "yookassa": {"enabled": False, "shop_id": "", "secret_key": ""}
    }
    
    STORAGE: StorageSettings = StorageSettings()
    
    FRONTEND_URL: str = "https://your-domain.com"
    
    DEBUG: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        env_nested_delimiter = "__"

    def __init__(self, **data: Any):
        super().__init__(**data)
        if not self.SQLALCHEMY_DATABASE_URI:
            self.SQLALCHEMY_DATABASE_URI = (
                f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
                f"{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
            )
        
        self.PAYMENT_PROVIDERS = {
            "stripe": {
                "enabled": self.STRIPE.enabled,
                "api_key": self.STRIPE.api_key,
                "webhook_secret": self.STRIPE.webhook_secret
            },
            "paypal": {
                "enabled": self.PAYPAL.enabled,
                "client_id": self.PAYPAL.client_id,
                "secret": self.PAYPAL.secret,
                "sandbox": self.PAYPAL.sandbox,
                "webhook_id": self.PAYPAL.webhook_id
            },
            "yookassa": {
                "enabled": self.YOOKASSA.enabled,
                "shop_id": self.YOOKASSA.shop_id,
                "secret_key": self.YOOKASSA.secret_key
            }
        }


settings = Settings()
