from app.core.config import settings

PLANS = {
    "free": {
        "tokens": 10000,
        "token_limit": 10000,
        "monthly_quota": 1000,
        "max_products": 20,
        "max_campaigns": 0,
        "channels": ["whatsapp"],
        "features": ["chat", "products", "flows"],
        "price_id": None
    },
    "pro": {
        "tokens": 100000,
        "price_id": settings.STRIPE_PRICE_PRO
    },
    "enterprise": {
        "tokens": None,  # unlimited
        "price_id": settings.STRIPE_PRICE_ENTERPRISE
    }
}
