from sqlalchemy import select
from app.models.system_settings import SystemSettings
from app.core.default_settings import DEFAULT_SETTINGS
from app.api.deps import redis_client

class SettingsService:

    @staticmethod
    async def get(db, key: str):
        if db is None:
            return DEFAULT_SETTINGS.get(key)

        cache_key = f"settings:{key}"
        cached = await redis_client.get(cache_key)
        if cached is not None:
            return cached

        res = await db.execute(
            select(SystemSettings).where(SystemSettings.key == key)
        )
        setting = res.scalar_one_or_none()

        if setting:
            await redis_client.setex(cache_key, 60, setting.value)
            return setting.value

        return DEFAULT_SETTINGS.get(key)

    @staticmethod
    async def set(db, key: str, value: str):
        res = await db.execute(
            select(SystemSettings).where(SystemSettings.key == key)
        )
        setting = res.scalar_one_or_none()

        if setting:
            setting.value = value
        else:
            db.add(SystemSettings(key=key, value=value))

        await redis_client.delete(f"settings:{key}")
