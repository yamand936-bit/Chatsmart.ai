from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.settings_service import SettingsService
from app.api.deps import get_current_admin

router = APIRouter(prefix="/system", tags=["System"])

ALLOWED_KEYS = [
    "platform_name",
    "billing_mode",
    "ai_provider",
    "ai_model",
    "support_phone",
    "free_tokens",
    "pro_tokens",
    "enterprise_tokens",
    "custom_ai_endpoint",
]

INTEGER_KEYS = {"free_tokens", "pro_tokens", "enterprise_tokens"}

@router.get("/settings")
async def get_settings(db: AsyncSession = Depends(get_db), admin: dict = Depends(get_current_admin)):
    result = {}
    for k in ALLOWED_KEYS:
        result[k] = await SettingsService.get(db, k)
    return result

@router.post("/settings")
async def update_settings(payload: dict, db: AsyncSession = Depends(get_db), admin: dict = Depends(get_current_admin)):
    for key, value in payload.items():
        if key not in ALLOWED_KEYS:
            raise HTTPException(400, f"Invalid key: {key}")
        if key in INTEGER_KEYS:
            try:
                int(value)
            except (ValueError, TypeError):
                raise HTTPException(400, f"'{key}' must be an integer")
        await SettingsService.set(db, key, str(value))
    await db.commit()
    return {"status": "updated"}
