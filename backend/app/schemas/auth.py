from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
import uuid

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: str
    role: str
    business_id: Optional[uuid.UUID] = None
