from datetime import datetime
from typing import Optional, List, Annotated
from pydantic import BaseModel, Field, BeforeValidator, field_serializer
from bson import ObjectId

# Define a custom type for ObjectId fields
def validate_object_id(v) -> ObjectId:
    if isinstance(v, ObjectId):
        return v
    if isinstance(v, str) and ObjectId.is_valid(v):
        return ObjectId(v)
    raise ValueError("Invalid ObjectId")

PyObjectId = Annotated[ObjectId, BeforeValidator(validate_object_id)]

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(CategoryBase):
    name: Optional[str] = None
    description: Optional[str] = None

class CategoryInDB(CategoryBase):
    id: PyObjectId = Field(default_factory=ObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }
    
    @field_serializer('id')
    def serialize_id(self, id: ObjectId) -> str:
        return str(id)

class Category(CategoryBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }
