from app.core.config import settings

PLANS = {
    "free": {
        "tokens": 10000,
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
