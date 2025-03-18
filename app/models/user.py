from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from app.models.object_id import PyObjectId

class UserBase(BaseModel):
    email: EmailStr
    username: str
    is_active: bool = True
    is_admin: bool = False

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_schema_extra": {
            "example": {
                "_id": "60d21b4967d0d8992e610c85",
                "email": "user@example.com",
                "username": "username",
                "hashed_password": "hashed_password",
                "is_active": True,
                "is_admin": False
            }
        }
    }

class User(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }
