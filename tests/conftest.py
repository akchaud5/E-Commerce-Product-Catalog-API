import asyncio
import pytest
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.testclient import TestClient
from typing import Generator, Any
from bson import ObjectId
import os

from app.main import app
from app.core.config import settings
from app.db.mongodb import database, get_collection
from app.services import user_service
from app.models.user import UserCreate


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    try:
        loop = asyncio.get_event_loop_policy().new_event_loop()
        asyncio.set_event_loop(loop)
        yield loop
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()


@pytest.fixture(scope="session")
def test_client() -> Generator[TestClient, Any, None]:
    """
    Create a FastAPI TestClient that uses the test database.
    """
    with TestClient(app) as client:
        yield client


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    """
    Create test database and collections, and clean up after tests.
    """
    # Use a test database with a different name
    test_db_name = "ecommerce_test"
    
    try:
        # For CI environment, use the exact URL provided
        if os.getenv("GITHUB_ACTIONS") == "true":
            test_mongodb_url = settings.MONGODB_URL
        # Handle different MongoDB URL formats (standard or Atlas)
        elif settings.MONGODB_URL.startswith('mongodb+srv://'):
            # For Atlas URLs, directly use the client with database name
            test_mongodb_url = settings.MONGODB_URL
        else:
            # For standard URLs, try to split off any existing database name
            # and append our test database name
            base_url = settings.MONGODB_URL
            if '/' in base_url[10:]:  # Skip the mongodb:// prefix
                base_url = settings.MONGODB_URL.rsplit('/', 1)[0]
            test_mongodb_url = f"{base_url}/{test_db_name}"
        
        # Connect to test database with increased timeout
        client = AsyncIOMotorClient(
            test_mongodb_url,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000
        )
        # Force a connection to verify it works
        await client.admin.command('ping')
        
        # Get database
        test_db = client[test_db_name]
        
        # Save original database
        original_database = database
        
        # Replace database with test database
        globals()["database"] = test_db
        
        # Create collections if they don't exist
        collections = await test_db.list_collection_names()
        if "users" not in collections:
            await test_db.create_collection("users")
        if "products" not in collections:
            await test_db.create_collection("products")
        if "categories" not in collections:
            await test_db.create_collection("categories")
        
        yield
        
        # Clean up: drop test database
        await client.drop_database(test_db_name)
        
        # Restore original database
        globals()["database"] = original_database
    
    except Exception as e:
        pytest.skip(f"MongoDB connection failed: {e}")
        yield None


@pytest_asyncio.fixture
async def sample_user():
    """
    Create a sample user for testing.
    """
    user_data = UserCreate(
        email="test@example.com",
        username="testuser",
        password="password123"
    )
    
    # Check if user already exists and delete it
    existing_user = await user_service.get_user_by_email(user_data.email)
    if existing_user:
        await database.users.delete_one({"_id": existing_user.id})
    
    user = await user_service.create_user(user_data)
    return user


@pytest_asyncio.fixture
async def admin_user():
    """
    Create an admin user for testing.
    """
    user_data = UserCreate(
        email="admin@example.com",
        username="adminuser",
        password="password123"
    )
    
    # Check if user already exists and delete it
    existing_user = await user_service.get_user_by_email(user_data.email)
    if existing_user:
        await database.users.delete_one({"_id": existing_user.id})
    
    user = await user_service.create_user(user_data)
    
    # Make user an admin
    await database.users.update_one(
        {"_id": user.id},
        {"$set": {"is_admin": True}}
    )
    
    # Get updated user
    user_dict = await database.users.find_one({"_id": user.id})
    return user_dict


@pytest_asyncio.fixture
async def auth_headers(sample_user):
    """
    Create auth headers for testing.
    """
    from app.core.security import create_access_token
    
    access_token = create_access_token(subject=str(sample_user.id))
    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture
async def admin_auth_headers(admin_user):
    """
    Create admin auth headers for testing.
    """
    from app.core.security import create_access_token
    
    access_token = create_access_token(subject=str(admin_user["_id"]))
    return {"Authorization": f"Bearer {access_token}"}