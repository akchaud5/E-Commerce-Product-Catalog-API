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
    # Don't raise an exception, allow the app to start with degraded functionality
    # This is especially useful for deployment environments where MongoDB might not be available immediately
    client = None

# Only get database if client connection succeeded
if client:
    # For MongoDB Atlas URLs that don't specify a database, use a fixed name
    database = client["ecommerce"]
    
    # Collections
    products_collection = database.products
    categories_collection = database.categories
    users_collection = database.users
else:
    # Define placeholders that will cause more specific errors if accessed
    database = None
    products_collection = None
    categories_collection = None
    users_collection = None

async def get_collection(collection_name: str):
    if database is None:
        raise ConnectionError("MongoDB connection not available")
    return database[collection_name]