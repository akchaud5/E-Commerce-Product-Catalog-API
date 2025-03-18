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

class ProductBase(BaseModel):
    name: str
    description: str
    price: float
    stock: int
    category_id: PyObjectId
    is_active: bool = True
    image_url: Optional[str] = None
    tags: List[str] = []

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    category_id: Optional[PyObjectId] = None
    is_active: Optional[bool] = None
    image_url: Optional[str] = None
    tags: Optional[List[str]] = None

class ProductInDB(ProductBase):
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
    
    @field_serializer('category_id')
    def serialize_category_id(self, category_id: ObjectId) -> str:
        return str(category_id)

class Product(ProductBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }
