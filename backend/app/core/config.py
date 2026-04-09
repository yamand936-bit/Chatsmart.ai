from pydantic_settings import BaseSettings
from typing import Optional, List, Union
from pydantic import AnyHttpUrl, validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "ChatSmart AI"
    
    # DB
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str
    
    # Security - NO default fallback allowed for JWT
    JWT_SECRET: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 60 minutes — matches cookie max_age
    IS_PRODUCTION: bool = False  # Set to True in production to enforce Secure cookie
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # AI
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # Intergrations Configuration Mode (mock | live)
    INTEGRATIONS_MODE: str = "live"
    
    # Telegram Integration (Global Fallbacks)
    TELEGRAM_BOT_TOKEN: str | None = None
    TELEGRAM_SECRET_TOKEN: str | None = None
    ADMIN_TELEGRAM_CHAT_ID: str | None = None

    # Meta Integration
    META_APP_ID: str | None = None
    META_APP_SECRET: str | None = None

    # TikTok Integration
    TIKTOK_CLIENT_KEY: str | None = None
    TIKTOK_CLIENT_SECRET: str | None = None

    # Stripe
    STRIPE_SECRET_KEY: str | None = None
    STRIPE_WEBHOOK_SECRET: str | None = None
    STRIPE_PRICE_PRO: str | None = None
    STRIPE_PRICE_ENTERPRISE: str | None = None

    # SMTP Integration (For Merchant Notifications)
    SMTP_HOST: str | None = None
    SMTP_PORT: int | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"

settings = Settings()

import pytz
