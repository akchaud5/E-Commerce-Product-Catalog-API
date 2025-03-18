from datetime import datetime
from typing import Optional, List, Annotated
from pydantic import BaseModel, Field, EmailStr, BeforeValidator, field_serializer
from bson import ObjectId
import json

# Define a custom type for ObjectId fields
def validate_object_id(v) -> ObjectId:
    if isinstance(v, ObjectId):
        return v
    if isinstance(v, str) and ObjectId.is_valid(v):
        return ObjectId(v)
    raise ValueError("Invalid ObjectId")

PyObjectId = Annotated[ObjectId, BeforeValidator(validate_object_id)]

class UserBase(BaseModel):
    email: EmailStr
    username: str
    is_active: bool = True
    is_admin: bool = False

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: PyObjectId = Field(default_factory=ObjectId, alias="_id")
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }
    
    @field_serializer('id')
    def serialize_id(self, id: ObjectId) -> str:
        return str(id)

class User(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }
