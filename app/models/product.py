from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.models.object_id import PyObjectId

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
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_schema_extra": {
            "example": {
                "_id": "60d21b4967d0d8992e610c85",
                "name": "Product Name",
                "description": "Product Description",
                "price": 99.99,
                "stock": 100,
                "category_id": "60d21b4967d0d8992e610c86",
                "is_active": True
            }
        }
    }

class Product(ProductBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }
