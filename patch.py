with open("backend/app/api/routers/merchant.py", "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace(
"""class SettingsUpdate(BaseModel):
    knowledge_base: Optional[str] = None
    bank_details: Optional[dict] = None
    primary_color: Optional[str] = None
    logo_url: Optional[str] = None
    sheet_url: Optional[str] = None
    business_type: Optional[str] = None
    notification_email: Optional[str] = None
    notification_telegram: Optional[str] = None
    staff_members: Optional[List[str]] = None""",
"""class SettingsUpdate(BaseModel):
    knowledge_base: Optional[str] = None
    bank_details: Optional[dict] = None
    primary_color: Optional[str] = None
    logo_url: Optional[str] = None
    sheet_url: Optional[str] = None
    business_type: Optional[str] = None
    notification_email: Optional[str] = None
    notification_telegram: Optional[str] = None
    staff_members: Optional[List[str]] = None
    setup_complete: Optional[bool] = None
    name: Optional[str] = None
    language: Optional[str] = None""")

text = text.replace(
"""            "notification_telegram": business.notification_telegram,
            "staff_members": business.staff_members or [],
            "active_features": active_features
        }""",
"""            "notification_telegram": business.notification_telegram,
            "staff_members": business.staff_members or [],
            "active_features": active_features,
            "setup_complete": business.setup_complete,
            "name": business.name,
            "language": business.language
        }""")

text = text.replace(
"""    if data.staff_members is not None:
         business.staff_members = data.staff_members
         
    await db.commit()""",
"""    if data.staff_members is not None:
         business.staff_members = data.staff_members
    if data.setup_complete is not None:
         business.setup_complete = data.setup_complete
    if data.name is not None:
         business.name = data.name
    if data.language is not None:
         business.language = data.language
         
    await db.commit()""")

with open("backend/app/api/routers/merchant.py", "w", encoding="utf-8") as f:
    f.write(text)
