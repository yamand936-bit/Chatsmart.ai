import sys
from pydantic_settings import BaseSettings
from typing import List, Union
from pydantic import AnyHttpUrl, validator

class Settings(BaseSettings):
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

s = Settings(BACKEND_CORS_ORIGINS='["https://smartchat-ai.org"]')
print(repr(s.BACKEND_CORS_ORIGINS[0]))
print(f"{s.BACKEND_CORS_ORIGINS[0]}/api/integrations/telegram/xyz/webhook")
