from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from app.db.mongodb import categories_collection
from app.models.category import CategoryInDB, CategoryCreate, CategoryUpdate

async def create_category(category: CategoryCreate) -> CategoryInDB:
    category_in_db = CategoryInDB(**category.dict())
    new_category = await categories_collection.insert_one(category_in_db.dict(by_alias=True))
    created_category = await categories_collection.find_one({"_id": new_category.inserted_id})
    return CategoryInDB(**created_category)

async def get_category_by_id(category_id: str) -> Optional[CategoryInDB]:
    if not ObjectId.is_valid(category_id):
        return None
    category_data = await categories_collection.find_one({"_id": ObjectId(category_id)})
    if category_data:
        return CategoryInDB(**category_data)
    return None

async def get_category_by_name(name: str) -> Optional[CategoryInDB]:
    category_data = await categories_collection.find_one({"name": name})
    if category_data:
        return CategoryInDB(**category_data)
    return None

async def update_category(category_id: str, update_data: Dict[str, Any]) -> Optional[CategoryInDB]:
    if not ObjectId.is_valid(category_id):
        return None
    
    update_data["updated_at"] = datetime.utcnow()
    
    await categories_collection.update_one(
        {"_id": ObjectId(category_id)},
        {"$set": update_data}
    )
    
    updated_category = await categories_collection.find_one({"_id": ObjectId(category_id)})
    if updated_category:
        return CategoryInDB(**updated_category)
    return None

async def delete_category(category_id: str) -> bool:
    if not ObjectId.is_valid(category_id):
        return False
    result = await categories_collection.delete_one({"_id": ObjectId(category_id)})
    return result.deleted_count > 0

async def get_all_categories(skip: int = 0, limit: int = 100) -> List[CategoryInDB]:
    categories = []
    cursor = categories_collection.find().skip(skip).limit(limit).sort("name", 1)
    async for document in cursor:
        categories.append(CategoryInDB(**document))
    return categories
