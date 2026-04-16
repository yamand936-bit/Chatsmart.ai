import asyncio
import datetime
import random
import uuid
from sqlalchemy.future import select
from sqlalchemy import func
from app.db.session import async_session_maker
from app.models.user import User
from app.models.business import Business
from app.models.domain import Product, Appointment
from app.core.security import get_password_hash

async def seed_demos():
    async with async_session_maker() as db:
        password_hashed = get_password_hash("demo123")

        # Define Demo accounts
        demos = [
            {
                "email": "retail@demo.com",
                "name": "Luxury Timepieces & Leather",
                "type": "retail",
                "tone": "Sales-driven",
                "bank": {"iban": "SA123456789", "bank_name": "Al Rajhi Bank", "currency": "SAR"},
                "kb": "\u0646\u062d\u0646 \u0645\u062a\u062c\u0631 \u0645\u062a\u062e\u0635\u0635 \u0641\u064a \u0628\u064a\u0639 \u0627\u0644\u0633\u0627\u0639\u0627\u062a \u0627\u0644\u0641\u0627\u062e\u0631\u0629 \u0648\u0627\u0644\u0645\u062d\u0627\u0641\u0638 \u0627\u0644\u062c\u0644\u062f\u064a\u0629. \n\u0633\u064a\u0627\u0633\u0629 \u0627\u0644\u0627\u0633\u062a\u0631\u062c\u0627\u0639: \u062e\u0644\u0627\u0644 14 \u064a\u0648\u0645 \u0645\u0646 \u062a\u0627\u0631\u064a\u062e \u0627\u0644\u0634\u0631\u0627\u0621 \u0628\u0634\u0631\u0637 \u0639\u062f\u0645 \u0627\u0644\u0627\u0633\u062a\u062e\u062f\u0627\u0645.\n\u0627\u0644\u062a\u0648\u0635\u064a\u0644: \u0645\u062c\u0627\u0646\u064a \u0644\u062c\u0645\u064a\u0639 \u0627\u0644\u0645\u0646\u0627\u0637\u0642 \u062e\u0644\u0627\u0644 2-3 \u0623\u064a\u0627\u0645 \u0639\u0645\u0644.\n\u062a\u0639\u0644\u064a\u0645\u0627\u062a \u0644\u0643 \u0643\u0628\u0627\u0626\u0639 \u0630\u0643\u0627\u0621 \u0627\u0635\u0637\u0646\u0627\u0639\u064a: \u0643\u0646 \u062d\u0645\u0627\u0633\u064a\u0627\u064b \u0648\u062a\u0634\u062c\u064a\u0639\u064a\u0627\u064b \u062c\u062f\u0627\u064b\u060c \u0631\u0643\u0632 \u0639\u0644\u0649 \u0623\u0646\u0627\u0642\u0629 \u0627\u0644\u0645\u0646\u062a\u062c \u0648\u062c\u0648\u062f\u062a\u0647\u060c \u0648\u0625\u0630\u0627 \u0637\u0644\u0628 \u0627\u0644\u0639\u0645\u064a\u0644 \u0633\u0627\u0639\u0629 \u0627\u0642\u062a\u0631\u062d \u0639\u0644\u064a\u0647 \u0645\u062d\u0641\u0638\u0629 \u062a\u0644\u064a\u0642 \u0628\u0647\u0627. \u062f\u0627\u0626\u0645\u0627\u064b \u062d\u0627\u0648\u0644 \u0625\u062a\u0645\u0627\u0645 \u0627\u0644\u0628\u064a\u0639 \u0645\u0628\u0627\u0634\u0631\u0629 \u0648\u0627\u0637\u0644\u0628 \u0628\u064a\u0627\u0646\u0627\u062a \u0627\u0644\u0634\u062d\u0646.",
                "item_type": "product",
                "items": [
                    {"name": f"\u0633\u0627\u0639\u0629 \u0631\u0648\u0644\u0643\u0633 \u0643\u0644\u0627\u0633\u064a\u0643 - \u0625\u0635\u062f\u0627\u0631 \u0645\u062d\u062f\u0648\u062f {i}", "price": 450.0 + (i*10), "desc": "\u0633\u0627\u0639\u0629 \u0641\u0627\u062e\u0631\u0629 \u0645\u0642\u0627\u0648\u0645\u0629 \u0644\u0644\u0645\u0627\u0621 \u0645\u0639 \u0636\u0645\u0627\u0646 \u0633\u0646\u062a\u064a\u0646.", "stock": 5} for i in range(1, 13)
                ] + [
                    {"name": f"\u0645\u062d\u0641\u0638\u0629 \u062c\u0644\u062f \u0637\u0628\u064a\u0639\u064a \u0625\u064a\u0637\u0627\u0644\u064a {i}", "price": 50.0 + (i*5), "desc": "\u0645\u062d\u0641\u0638\u0629 \u0631\u062c\u0627\u0644\u064a\u0629 \u0623\u0646\u064a\u0642\u0629 \u062a\u062a\u0633\u0639 \u0644\u0640 10 \u0628\u0637\u0627\u0642\u0627\u062a.", "stock": 10} for i in range(1, 14)
                ]
            },
            {
                "email": "dental@demo.com",
                "name": "SmileCare Clinic - \u0639\u064a\u0627\u062f\u0629 \u0633\u0645\u0627\u064a\u0644 \u0643\u064a\u0631 \u0644\u0644\u0623\u0633\u0646\u0627\u0646",
                "type": "services",
                "tone": "Professional",
                "bank": {"iban": "", "bank_name": "Cash/Card at Clinic", "currency": "USD"},
                "kb": "\u0646\u062d\u0646 \u0639\u064a\u0627\u062f\u0629 \u0623\u0633\u0646\u0627\u0646 \u0645\u062a\u062e\u0635\u0635\u0629. \u0627\u0644\u0623\u0637\u0628\u0627\u0621 \u0627\u0644\u0645\u062a\u0627\u062d\u0648\u0646: \u062f. \u0623\u062d\u0645\u062f\u060c \u062f. \u0633\u0627\u0631\u0629\u060c \u062f. \u062e\u0627\u0644\u062f.\n\u0633\u0627\u0639\u0627\u062a \u0627\u0644\u0639\u0645\u0644: \u0645\u0646 10 \u0635\u0628\u0627\u062d\u0627\u064b \u062d\u062a\u0649 8 \u0645\u0633\u0627\u0621\u064b \u064a\u0648\u0645\u064a\u0627\u064b \u0639\u062f\u0627 \u0627\u0644\u062c\u0645\u0639\u0629.\n\u0633\u064a\u0627\u0633\u0629 \u0627\u0644\u0639\u064a\u0627\u062f\u0629: \u064a\u062a\u0645 \u062a\u0623\u0643\u064a\u062f \u0627\u0644\u0645\u0648\u0639\u062f \u0645\u0628\u062f\u0626\u064a\u0627\u064b \u0648\u064a\u062c\u0628 \u0627\u0644\u062d\u0636\u0648\u0631 \u0642\u0628\u0644 15 \u062f\u0642\u064a\u0642\u0629. \u0644\u0627 \u062a\u0648\u062c\u062f \u0631\u0633\u0648\u0645 \u0639\u0644\u0649 \u0627\u0644\u0625\u0644\u063a\u0627\u0621 \u0642\u0628\u0644 24 \u0633\u0627\u0639\u0629.\n\u062a\u0639\u0644\u064a\u0645\u0627\u062a \u0645\u0633\u0627\u0639\u062f \u0627\u0644\u0630\u0643\u0627\u0621 \u0627\u0644\u0627\u0635\u0637\u0646\u0627\u0639\u064a: \u0643\u0646 \u0644\u0637\u064a\u0641\u0627\u064b \u0648\u0645\u0647\u0646\u064a\u0627\u064b \u062c\u062f\u0627\u064b. \u0627\u0633\u0623\u0644 \u0627\u0644\u0645\u0631\u064a\u0636 \u0639\u0646 \u0646\u0648\u0639 \u0627\u0644\u0623\u0644\u0645 \u0623\u0648 \u0627\u0644\u062e\u062f\u0645\u0629 \u0627\u0644\u062a\u064a \u064a\u062d\u062a\u0627\u062c\u0647\u0627\u060c \u062b\u0645 \u0627\u0639\u0631\u0636 \u0639\u0644\u064a\u0647 \u0623\u0642\u0631\u0628 \u0648\u0642\u062a \u0645\u062a\u0627\u062d \u0648\u0642\u0645 \u0628\u062c\u062f\u0648\u0644\u0629 \u0627\u0644\u0645\u0648\u0639\u062f \u0645\u0628\u0627\u0634\u0631\u0629.",
                "item_type": "service",
                "items": [
                    {"name": "\u062e\u0644\u0639 \u0636\u0631\u0633 / \u0633\u0646 (Tooth Extraction)", "price": 20.0, "desc": "\u062e\u0644\u0639 \u0622\u0645\u0646 \u0628\u062f\u0648\u0646 \u0623\u0644\u0645 \u0645\u0639 \u062a\u062e\u062f\u064a\u0631 \u0645\u0648\u0636\u0639\u064a.", "duration": 30},
                    {"name": "\u062a\u0644\u0628\u064a\u0633 \u0623\u0633\u0646\u0627\u0646 \u0632\u064a\u0631\u0643\u0648\u0646", "price": 50.0, "desc": "\u062a\u0631\u0643\u064a\u0628\u0629 \u0632\u064a\u0631\u0643\u0648\u0646 \u0623\u0644\u0645\u0627\u0646\u064a\u0629 \u0639\u0627\u0644\u064a\u0629 \u0627\u0644\u062c\u0648\u062f\u0629.", "duration": 60},
                    {"name": "\u062a\u0646\u0638\u064a\u0641 \u0627\u0644\u062c\u064a\u0631 \u0648\u062a\u0644\u0645\u064a\u0639 \u0627\u0644\u0623\u0633\u0646\u0627\u0646", "price": 15.0, "desc": "\u0625\u0632\u0627\u0644\u0629 \u0627\u0644\u0631\u0648\u0627\u0633\u0628 \u0627\u0644\u062c\u064a\u0631\u064a\u0629 \u0648\u062a\u0644\u0645\u064a\u0639 \u0627\u0644\u0645\u064a\u0646\u0627.", "duration": 30},
                    {"name": "\u062d\u0634\u0648\u0629 \u062a\u062c\u0645\u064a\u0644\u064a\u0629 \u0644\u0644\u0623\u0633\u0646\u0627\u0646 \u0627\u0644\u0623\u0645\u0627\u0645\u064a\u0629", "price": 30.0, "desc": "\u062d\u0634\u0648\u0629 \u0644\u064a\u0632\u0631 \u0645\u0637\u0627\u0628\u0642\u0629 \u0644\u0644\u0648\u0646 \u0627\u0644\u0633\u0646 \u0627\u0644\u0637\u0628\u064a\u0639\u064a.", "duration": 45},
                    {"name": "\u062a\u0628\u064a\u064a\u0636 \u0627\u0644\u0623\u0633\u0646\u0627\u0646 \u0628\u0627\u0644\u0644\u064a\u0632\u0631 (\u0627\u0644\u062c\u0644\u0633\u0629)", "price": 70.0, "desc": "\u062a\u0628\u064a\u064a\u0636 \u0633\u0631\u064a\u0639 \u0648\u0622\u0645\u0646 \u0628\u062a\u0642\u0646\u064a\u0629 \u0632\u0648\u0648\u0645.", "duration": 60},
                    {"name": "\u062a\u0642\u0648\u064a\u0645 \u0627\u0644\u0623\u0633\u0646\u0627\u0646 (\u062f\u0641\u0639\u0629 \u0623\u0648\u0644\u0649)", "price": 200.0, "desc": "\u062a\u0631\u0643\u064a\u0628 \u0623\u0642\u0648\u0627\u0633 \u0627\u0644\u062a\u0642\u0648\u064a\u0645 \u0648\u0628\u062f\u0621 \u0627\u0644\u062e\u0637\u0629 \u0627\u0644\u0639\u0644\u0627\u062c\u064a\u0629.", "duration": 90},
                    {"name": "\u0639\u0644\u0627\u062c \u0639\u0635\u0628 \u062c\u0630\u0648\u0631", "price": 80.0, "desc": "\u0628\u0648\u0627\u0633\u0637\u0629 \u0623\u062d\u062f\u062b \u0627\u0644\u0623\u062c\u0647\u0632\u0629 \u0627\u0644\u0631\u0648\u062a\u0627\u0631\u064a \u0644\u0645\u0646\u0639 \u0627\u0644\u0623\u0644\u0645.", "duration": 60},
                    {"name": "\u0627\u0633\u062a\u0634\u0627\u0631\u0629 \u0637\u0628\u064a\u0629 \u0645\u062c\u0627\u0646\u064a\u0629", "price": 0.0, "desc": "\u0641\u062d\u0635 \u0637\u0628\u064a \u0645\u0628\u062f\u0626\u064a \u0648\u062a\u0635\u0648\u064a\u0631 \u0623\u0634\u0639\u0629 \u0625\u0646 \u0644\u0632\u0645 \u0627\u0644\u0623\u0645\u0631.", "duration": 15},
                ]
            },
            {
                "email": "hotel@demo.com",
                "name": "Blue Waves Boutique Hotel - \u0641\u0646\u062f\u0642 \u0623\u0645\u0648\u0627\u062c",
                "type": "services",
                "tone": "Friendly",
                "bank": {"iban": "TR987654321", "bank_name": "Garanti Bank", "currency": "USD"},
                "kb": "\u0623\u0647\u0644\u0627\u064b \u0628\u0643 \u0641\u064a \u0641\u0646\u062f\u0642 \u0623\u0645\u0648\u0627\u062c \u0627\u0644\u0635\u063a\u064a\u0631 \u0627\u0644\u0645\u0637\u0644 \u0639\u0644\u0649 \u0627\u0644\u0628\u062d\u0631.\n\u0645\u0639\u0644\u0648\u0645\u0627\u062a \u0627\u0644\u0641\u0646\u062f\u0642: \u064a\u0642\u0639 \u0627\u0644\u0641\u0646\u062f\u0642 \u0639\u0644\u0649 \u0627\u0644\u0634\u0627\u0637\u0626 \u0645\u0628\u0627\u0634\u0631\u0629. \u062a\u0633\u062c\u064a\u0644 \u0627\u0644\u062f\u062e\u0648\u0644 \u0627\u0644\u0633\u0627\u0639\u0629 2 \u0645\u0633\u0627\u0621\u064b\u060c \u0648\u0627\u0644\u062e\u0631\u0648\u062c \u0627\u0644\u0633\u0627\u0639\u0629 12 \u0638\u0647\u0631\u0627\u064b.\n\u0627\u0644\u0625\u0641\u0637\u0627\u0631 \u0645\u062c\u0627\u0646\u064a \u0644\u062c\u0645\u064a\u0639 \u0627\u0644\u0646\u0632\u0644\u0627\u0621.\n\u0633\u064a\u0627\u0633\u0629 \u0627\u0644\u0625\u0644\u063a\u0627\u0621: \u0627\u0633\u062a\u0631\u062f\u0627\u062f \u0643\u0627\u0645\u0644 \u0625\u0630\u0627 \u062a\u0645 \u0627\u0644\u0625\u0644\u063a\u0627\u0621 \u0642\u0628\u0644 72 \u0633\u0627\u0639\u0629.\n\u0634\u0631\u0648\u0637: \u0644\u0627 \u064a\u064f\u0633\u0645\u062d \u0628\u0627\u0635\u0637\u062d\u0627\u0628 \u0627\u0644\u062d\u064a\u0648\u0627\u0646\u0627\u062a \u0627\u0644\u0623\u0644\u064a\u0641\u0629.\n\u062a\u0639\u0644\u064a\u0645\u0627\u062a \u0644\u0643 \u0643\u0628\u0627\u0626\u0639 \u0630\u0643\u0627\u0621 \u0627\u0635\u0637\u0646\u0627\u0639\u064a: \u062a\u062d\u062f\u062b \u0628\u0644\u0647\u062c\u0629 \u0645\u0631\u062d\u0628\u0629 \u0648\u062f\u0627\u0641\u0626\u0629 \u062c\u062f\u0627\u064b \u0643\u0623\u0646\u0643 \u062a\u0633\u062a\u0642\u0628\u0644 \u0636\u064a\u0641\u0627\u064b \u0641\u064a \u0645\u0646\u0632\u0644\u0643. \u0627\u0633\u0623\u0644\u0647\u0645 \u0639\u0646 \u062a\u0648\u0627\u0631\u064a\u062e \u0625\u0642\u0627\u0645\u062a\u0647\u0645 \u0648\u0639\u062f\u062f \u0627\u0644\u0623\u0634\u062e\u0627\u0635 \u0648\u0628\u0646\u0627\u0621 \u0639\u0644\u064a\u0647 \u0631\u0634\u062d \u0627\u0644\u063a\u0631\u0641\u0629 \u0627\u0644\u0645\u0646\u0627\u0633\u0628\u0629.",
                "item_type": "service",
                "items": [
                    {"name": "\u063a\u0631\u0641\u0629 \u0645\u0641\u0631\u062f\u0629 \u0642\u064a\u0627\u0633\u064a\u0629 (\u0645\u0639 \u0625\u0641\u0637\u0627\u0631)", "price": 80.0, "desc": "\u063a\u0631\u0641\u0629 \u0645\u0631\u064a\u062d\u0629 \u0644\u0634\u062e\u0635 \u0648\u0627\u062d\u062f.", "duration": 1440},
                    {"name": "\u063a\u0631\u0641\u0629 \u0645\u0632\u062f\u0648\u062c\u0629 \u0625\u0637\u0644\u0627\u0644\u0629 \u0639\u0644\u0649 \u0627\u0644\u062d\u062f\u064a\u0642\u0629", "price": 120.0, "desc": "\u0645\u062b\u0627\u0644\u064a\u0629 \u0644\u0644\u0623\u0632\u0648\u0627\u062c\u060c \u062a\u062a\u0633\u0639 \u0644\u0634\u062e\u0635\u064a\u0646.", "duration": 1440},
                    {"name": "\u063a\u0631\u0641\u0629 \u0645\u0632\u062f\u0648\u062c\u0629 \u0625\u0637\u0644\u0627\u0644\u0629 \u0645\u0628\u0627\u0634\u0631\u0629 \u0639\u0644\u0649 \u0627\u0644\u0628\u062d\u0631", "price": 150.0, "desc": "\u0625\u0637\u0644\u0627\u0644\u0629 \u0628\u0627\u0646\u0648\u0631\u0627\u0645\u064a\u0629 \u0631\u0627\u0626\u0639\u0629 \u0645\u0639 \u0634\u0631\u0641\u0629 \u062e\u0627\u0635\u0629.", "duration": 1440},
                    {"name": "\u062c\u0646\u0627\u062d \u0639\u0627\u0626\u0644\u064a 1 \u063a\u0631\u0641\u0629 \u0648\u0635\u0627\u0644\u0629", "price": 250.0, "desc": "\u064a\u062a\u0633\u0639 \u062d\u062a\u0649 4 \u0623\u0634\u062e\u0627\u0635\u060c \u0645\u0637\u0628\u062e \u0635\u063a\u064a\u0631.", "duration": 1440},
                    {"name": "\u0641\u064a\u0644\u0627 \u0634\u0627\u0637\u0626\u064a\u0629 \u0628\u0645\u0633\u0627\u0628\u062d \u062e\u0627\u0635\u0629", "price": 400.0, "desc": "\u062e\u0635\u0648\u0635\u064a\u0629 \u062a\u0627\u0645\u0629\u060c \u0645\u062b\u0627\u0644\u064a\u0629 \u0644\u0644\u0639\u0631\u0633\u0627\u0646.", "duration": 1440},
                ]
            }
        ]

        from datetime import date, timedelta
        current_date_utc = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        start_of_month = current_date_utc.replace(day=1, hour=0, minute=0, second=0)
        
        # Determine number of days in the current month
        next_month = start_of_month.replace(day=28) + timedelta(days=4)
        last_day_of_month = next_month - timedelta(days=next_month.day)
        total_days = last_day_of_month.day
        
        for demo in demos:
            # 1. Check or Create User
            u_res = await db.execute(select(User).where(User.email == demo["email"]))
            user = u_res.scalar_one_or_none()
            if not user:
                user = User(
                    email=demo["email"],
                    hashed_password=password_hashed
                )
                db.add(user)
                await db.flush() # get id
            
            # 2. Check or Create Business
            b_res = await db.execute(select(Business).where(Business.name == demo["name"]))
            business = b_res.scalar_one_or_none()
            if not business:
                business = Business(
                    name=demo["name"],
                    business_type=demo["type"],
                    ai_tone=demo["tone"],
                    knowledge_base=demo["kb"],
                    bank_details=demo["bank"],
                    status="active",
                    plan_name="pro"
                )
                db.add(business)
                await db.flush()
                
                # Assign user to this business
                user.business_id = business.id
                db.add(user)
                await db.flush()
                
            # Clear existing items to avoid duplicates on bad runs
            await db.execute(Product.__table__.delete().where(Product.business_id == business.id))
            
            # Add Items
            for idx, item in enumerate(demo["items"]):
                images = [
                    "https://images.unsplash.com/photo-1523275335684-37898b6baf30",
                    "https://images.unsplash.com/photo-1546868871-7041f2a55e12",
                    "https://images.unsplash.com/photo-1622434641406-a158123450f9"
                ]
                img = images[idx % len(images)] if demo["item_type"] == "product" else None
                p = Product(
                    business_id=business.id,
                    name=item["name"],
                    item_type=demo["item_type"],
                    price=item["price"],
                    description=item["desc"],
                    duration=item.get("duration"),
                    is_active=True,
                    image_url=img
                )
                db.add(p)

            # Generate 40% appointments for Dental
            if "Dental" in demo["name"]:
                await db.execute(Appointment.__table__.delete().where(Appointment.business_id == business.id))
                
                # 40% of standard 8 slots a day x total days (approx roughly 3 appointments per day)
                for day_offset in range(total_days):
                    dt = start_of_month + timedelta(days=day_offset)
                    if dt.weekday() == 4: # Skip Fridays
                        continue
                        
                    # Let's say 4 appointments per active day
                    for hour in [10, 12, 14, 16]:
                        if random.random() < 0.40: # 40% chance to book
                            # Mock Customer
                            from app.models.domain import Customer
                            c_id = uuid.uuid4()
                            cust = Customer(
                                id=c_id,
                                business_id=business.id,
                                platform="system",
                                external_id=f"seed_{c_id}",
                                name=f"Mocker {random.randint(100, 999)}",
                                phone=f"+96650000{random.randint(1000, 9999)}"
                            )
                            db.add(cust)
                            await db.flush()
                            
                            start_t = dt.replace(hour=hour)
                            end_t = start_t + timedelta(minutes=45)
                            appt = Appointment(
                                business_id=business.id,
                                customer_id=cust.id,
                                title=f"Dental Service - Dr. {random.choice(['Ahmed', 'Sara', 'Khalid'])}",
                                start_time=start_t,
                                end_time=end_t,
                                status="confirmed",
                                notes="Seeded booked appointment"
                            )
                            db.add(appt)
                            
            await db.commit()
            print(f"\u2705 Seeded {demo['name']} successfully.")

if __name__ == "__main__":
    asyncio.run(seed_demos())
