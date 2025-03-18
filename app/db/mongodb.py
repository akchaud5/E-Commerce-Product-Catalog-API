import motor.motor_asyncio
from app.core.config import settings

client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)
database = client.get_database()

async def get_collection(collection_name: str):
    return database[collection_name]

# Collections
products_collection = database.products
categories_collection = database.categories
users_collection = database.users