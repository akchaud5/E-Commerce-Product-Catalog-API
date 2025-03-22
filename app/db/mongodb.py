import motor.motor_asyncio
import logging
import asyncio
from app.core.config import settings
import functools
from typing import Optional

# Global variables for lazy initialization
client = None
database = None
products_collection = None
categories_collection = None
users_collection = None

def get_db_name(url: str) -> str:
    """Extract database name from MongoDB URL"""
    db_name = "ecommerce"
    
    # Handle both standard and Atlas connection strings
    if url.startswith('mongodb://') and '/' in url[10:]:
        parts = url.split('/')
        if len(parts) > 3 and parts[3]:
            potential_db = parts[3].split('?')[0]  # Remove query parameters if any
            if potential_db:
                db_name = potential_db
    
    return db_name

async def get_client() -> Optional[motor.motor_asyncio.AsyncIOMotorClient]:
    """Get a MongoDB client using the current event loop"""
    global client
    
    # Return existing client if already initialized
    if client is not None:
        return client
    
    # Set default MongoDB URL if not provided or invalid
    mongo_url = settings.MONGODB_URL
    if not mongo_url or not (mongo_url.startswith('mongodb://') or mongo_url.startswith('mongodb+srv://')):
        logging.warning(f"Invalid MongoDB URL provided, using default local MongoDB")
        mongo_url = "mongodb://localhost:27017/ecommerce"
    
    try:
        # Create a new client with the current event loop
        loop = asyncio.get_event_loop()
        new_client = motor.motor_asyncio.AsyncIOMotorClient(
            mongo_url,
            io_loop=loop,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000
        )
        
        # Ping the server to confirm connection
        await new_client.admin.command('ping')
        logging.info("Successfully connected to MongoDB")
        
        # Update global client
        client = new_client
        return client
    except Exception as e:
        logging.error(f"MongoDB connection error: {e}")
        return None

async def get_database():
    """Get the database using the current event loop"""
    global database, client
    
    if database is not None:
        return database
    
    # Get client
    client = await get_client()
    if client is None:
        return None
    
    # Extract database name from MONGODB_URL
    db_name = get_db_name(settings.MONGODB_URL)
    
    # Set global database
    database = client[db_name]
    return database

async def get_products_collection():
    """Get the products collection using the current event loop"""
    global products_collection
    
    if products_collection is not None:
        return products_collection
    
    db = await get_database()
    if db is None:
        return None
    
    products_collection = db.products
    return products_collection

async def get_categories_collection():
    """Get the categories collection using the current event loop"""
    global categories_collection
    
    if categories_collection is not None:
        return categories_collection
    
    db = await get_database()
    if db is None:
        return None
    
    categories_collection = db.categories
    return categories_collection

async def get_users_collection():
    """Get the users collection using the current event loop"""
    global users_collection
    
    if users_collection is not None:
        return users_collection
    
    db = await get_database()
    if db is None:
        return None
    
    users_collection = db.users
    return users_collection

async def get_collection(collection_name: str):
    """Get a collection by name using the current event loop"""
    db = await get_database()
    if db is None:
        raise ConnectionError("MongoDB connection not available")
    
    return db[collection_name]