from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from app.db.mongodb import get_products_collection
from app.models.product import ProductInDB, ProductCreate, ProductUpdate

async def create_product(product: ProductCreate) -> ProductInDB:
    product_data = product.dict()
    
    # Convert string category_id to ObjectId
    if isinstance(product_data["category_id"], str) and ObjectId.is_valid(product_data["category_id"]):
        product_data["category_id"] = ObjectId(product_data["category_id"])
    
    product_in_db = ProductInDB(**product_data)
    collection = await get_products_collection()
    new_product = await collection.insert_one(product_in_db.dict(by_alias=True))
    created_product = await collection.find_one({"_id": new_product.inserted_id})
    return ProductInDB(**created_product)

async def get_product_by_id(product_id: str) -> Optional[ProductInDB]:
    if not ObjectId.is_valid(product_id):
        return None
    collection = await get_products_collection()
    product_data = await collection.find_one({"_id": ObjectId(product_id)})
    if product_data:
        return ProductInDB(**product_data)
    return None

async def update_product(product_id: str, update_data: Dict[str, Any]) -> Optional[ProductInDB]:
    if not ObjectId.is_valid(product_id):
        return None
    
    # Convert string category_id to ObjectId if it exists in update_data
    if "category_id" in update_data and isinstance(update_data["category_id"], str) and ObjectId.is_valid(update_data["category_id"]):
        update_data["category_id"] = ObjectId(update_data["category_id"])
    
    update_data["updated_at"] = datetime.utcnow()
    
    collection = await get_products_collection()
    await collection.update_one(
        {"_id": ObjectId(product_id)},
        {"$set": update_data}
    )
    
    updated_product = await collection.find_one({"_id": ObjectId(product_id)})
    if updated_product:
        return ProductInDB(**updated_product)
    return None

async def delete_product(product_id: str) -> bool:
    if not ObjectId.is_valid(product_id):
        return False
    collection = await get_products_collection()
    result = await collection.delete_one({"_id": ObjectId(product_id)})
    return result.deleted_count > 0

async def get_all_products(skip: int = 0, limit: int = 100, filter_params: Dict[str, Any] = None) -> List[ProductInDB]:
    query = filter_params or {}
    
    # Convert string category_id to ObjectId if it exists in filter_params
    if "category_id" in query and isinstance(query["category_id"], str) and ObjectId.is_valid(query["category_id"]):
        query["category_id"] = ObjectId(query["category_id"])
    
    products = []
    collection = await get_products_collection()
    cursor = collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
    async for document in cursor:
        products.append(ProductInDB(**document))
    return products

async def search_products(search_term: str, skip: int = 0, limit: int = 100) -> List[ProductInDB]:
    query = {
        "$or": [
            {"name": {"$regex": search_term, "$options": "i"}},
            {"description": {"$regex": search_term, "$options": "i"}},
            {"tags": {"$in": [search_term]}}
        ]
    }
    
    products = []
    collection = await get_products_collection()
    cursor = collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
    async for document in cursor:
        products.append(ProductInDB(**document))
    return products

async def get_products_by_category(category_id: str, skip: int = 0, limit: int = 100) -> List[ProductInDB]:
    if not ObjectId.is_valid(category_id):
        return []
    
    query = {"category_id": ObjectId(category_id)}
    products = []
    collection = await get_products_collection()
    cursor = collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
    async for document in cursor:
        products.append(ProductInDB(**document))
    return products
