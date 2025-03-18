from typing import Optional, List
from pydantic import BaseModel

class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    stock: int
    category_id: str
    is_active: bool = True
    image_url: Optional[str] = None
    tags: List[str] = []

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    category_id: Optional[str] = None
    is_active: Optional[bool] = None
    image_url: Optional[str] = None
    tags: Optional[List[str]] = None

class ProductResponse(BaseModel):
    id: str
    name: str
    description: str
    price: float
    stock: int
    category_id: str
    is_active: bool
    image_url: Optional[str]
    tags: List[str]
    created_at: str
    updated_at: str
