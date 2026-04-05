import stripe
from app.core.config import settings
from typing import Optional

# Initialize stripe key
if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY

async def create_customer(email: str) -> Optional[str]:
    """Create a new Stripe Customer and return the customer_id."""
    if not settings.STRIPE_SECRET_KEY:
        return None
    try:
        customer = stripe.Customer.create(email=email)
        return customer.id
    except Exception as e:
        print(f"Stripe setup error: {e}")
        return None

async def create_checkout_session(business_id: str, plan_name: str, price_id: str, customer_id: Optional[str] = None) -> Optional[str]:
    """Create a Stripe Checkout Session for a given plan and business_id."""
    if not settings.STRIPE_SECRET_KEY:
        # Mock behavior for local testing if no keys are available
        return f"https://mock-stripe.com/checkout/{business_id}/{plan_name}"
        
    try:
        session_params = {
            "payment_method_types": ["card"],
            "line_items": [{"price": price_id, "quantity": 1}],
            "mode": "subscription",
            "success_url": f"http://localhost:3000/admin?checkout=success",
            "cancel_url": f"http://localhost:3000/admin?checkout=cancel",
            "metadata": {
                "business_id": str(business_id),
                "plan": plan_name
            }
        }
        
        if customer_id:
            session_params["customer"] = customer_id

        session = stripe.checkout.Session.create(**session_params)
        return session.url
    except Exception as e:
        print(f"Stripe checkout error: {e}")
        return None

async def cancel_subscription(subscription_id: str) -> bool:
    """Cancel a Stripe Subscription."""
    if not settings.STRIPE_SECRET_KEY:
        return True
        
    try:
        stripe.Subscription.delete(subscription_id)
        return True
    except Exception as e:
        print(f"Stripe cancellation error: {e}")
        return False
