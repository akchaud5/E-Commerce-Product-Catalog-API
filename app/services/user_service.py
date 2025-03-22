from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from app.db.mongodb import get_users_collection
from app.core.security import get_password_hash, verify_password
from app.models.user import UserInDB, UserCreate, User

async def get_user_by_email(email: str) -> Optional[UserInDB]:
    collection = await get_users_collection()
    user_data = await collection.find_one({"email": email})
    if user_data:
        return UserInDB(**user_data)
    return None

async def get_user_by_username(username: str) -> Optional[UserInDB]:
    collection = await get_users_collection()
    user_data = await collection.find_one({"username": username})
    if user_data:
        return UserInDB(**user_data)
    return None

async def get_user_by_id(user_id: str) -> Optional[UserInDB]:
    if not ObjectId.is_valid(user_id):
        return None
    collection = await get_users_collection()
    user_data = await collection.find_one({"_id": ObjectId(user_id)})
    if user_data:
        return UserInDB(**user_data)
    return None

async def create_user(user: UserCreate) -> UserInDB:
    user_in_db = UserInDB(
        email=user.email,
        username=user.username,
        hashed_password=get_password_hash(user.password),
        is_active=True,
        is_admin=False,
    )
    
    collection = await get_users_collection()
    new_user = await collection.insert_one(user_in_db.dict(by_alias=True))
    created_user = await collection.find_one({"_id": new_user.inserted_id})
    return UserInDB(**created_user)

async def authenticate_user(email: str, password: str) -> Optional[UserInDB]:
    user = await get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

async def update_user(user_id: str, update_data: dict) -> Optional[UserInDB]:
    if not ObjectId.is_valid(user_id):
        return None
        
    # Handle password update separately
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    update_data["updated_at"] = datetime.utcnow()
    
    collection = await get_users_collection()
    await collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )
    
    updated_user = await collection.find_one({"_id": ObjectId(user_id)})
    if updated_user:
        return UserInDB(**updated_user)
    return None

async def get_all_users(skip: int = 0, limit: int = 100) -> List[UserInDB]:
    users = []
    collection = await get_users_collection()
    cursor = collection.find().skip(skip).limit(limit)
    async for document in cursor:
        users.append(UserInDB(**document))
    return users
