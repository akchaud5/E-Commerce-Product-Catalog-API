import motor.motor_asyncio
import logging
from app.core.config import settings

# Set default MongoDB URL if not provided or invalid
mongo_url = settings.MONGODB_URL
if not mongo_url or not (mongo_url.startswith('mongodb://') or mongo_url.startswith('mongodb+srv://')):
    logging.warning(f"Invalid MongoDB URL provided, using default local MongoDB")
    mongo_url = "mongodb://localhost:27017/ecommerce"

try:
    client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
    # Ping the server to confirm connection
    client.admin.command('ping')
    logging.info("Successfully connected to MongoDB")
except Exception as e:
    logging.error(f"MongoDB connection error: {e}")
    raise

database = client.get_database()

async def get_collection(collection_name: str):
    return database[collection_name]

# Collections
products_collection = database.products
categories_collection = database.categories
users_collection = database.users