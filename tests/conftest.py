import asyncio
import pytest
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from typing import Generator, Any, AsyncGenerator
from bson import ObjectId
import os

from app.main import app
from app.core.config import settings
from app.db.mongodb import get_collection
from app.services import user_service
from app.models.user import UserCreate


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Fixture that provides an async httpx client connected to the app.
    This fixture uses ASGITransport explicitly to avoid the deprecation warning.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


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
        
        # Get current event loop
        loop = asyncio.get_event_loop()
        
        # Connect to test database with increased timeout
        test_client = AsyncIOMotorClient(
            test_mongodb_url,
            io_loop=loop,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000
        )
        
        # Force a connection to verify it works
        await test_client.admin.command('ping')
        
        # Get test database
        test_db = test_client[test_db_name]
        
        # Create collections if they don't exist
        collections = await test_db.list_collection_names()
        if "users" not in collections:
            await test_db.create_collection("users")
        if "products" not in collections:
            await test_db.create_collection("products")
        if "categories" not in collections:
            await test_db.create_collection("categories")
        
        # Monkey patch the get functions to return test values during tests
        async def get_test_client():
            return test_client
            
        async def get_test_database():
            return test_db
            
        async def get_test_products_collection():
            return test_db.products
            
        async def get_test_categories_collection():
            return test_db.categories
            
        async def get_test_users_collection():
            return test_db.users
        
        # Patch the module
        import app.db.mongodb
        
        # Save the original functions
        original_get_client = app.db.mongodb.get_client
        original_get_database = app.db.mongodb.get_database
        original_get_products_collection = app.db.mongodb.get_products_collection
        original_get_categories_collection = app.db.mongodb.get_categories_collection
        original_get_users_collection = app.db.mongodb.get_users_collection
        
        # Replace with test functions
        app.db.mongodb.get_client = get_test_client
        app.db.mongodb.get_database = get_test_database
        app.db.mongodb.get_products_collection = get_test_products_collection
        app.db.mongodb.get_categories_collection = get_test_categories_collection
        app.db.mongodb.get_users_collection = get_test_users_collection
        
        # Initialize the global variables for tests that directly use them
        app.db.mongodb.client = test_client
        app.db.mongodb.database = test_db
        app.db.mongodb.products_collection = test_db.products
        app.db.mongodb.categories_collection = test_db.categories
        app.db.mongodb.users_collection = test_db.users
        
        # Set a reference to the db in app for integration tests
        app.db = type('DB', (), {})()
        app.db.mongodb = type('MongoDB', (), {})()
        app.db.mongodb.get_client = get_test_client
        app.db.mongodb.get_database = get_test_database
        app.db.mongodb.get_products_collection = get_test_products_collection
        app.db.mongodb.get_categories_collection = get_test_categories_collection
        app.db.mongodb.get_users_collection = get_test_users_collection
        app.db.mongodb.client = test_client
        app.db.mongodb.database = test_db
        
        # Setup complete, yield control back to the tests
        yield
        
        # Clean up: drop test database
        await test_client.drop_database(test_db_name)
        
        # Restore original functions
        app.db.mongodb.get_client = original_get_client
        app.db.mongodb.get_database = original_get_database
        app.db.mongodb.get_products_collection = original_get_products_collection
        app.db.mongodb.get_categories_collection = original_get_categories_collection
        app.db.mongodb.get_users_collection = original_get_users_collection
        
        # Remove app.db
        if hasattr(app, 'db'):
            delattr(app, 'db')
        
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
        users_collection = await get_collection("users")
        await users_collection.delete_one({"_id": existing_user.id})
    
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
        users_collection = await get_collection("users")
        await users_collection.delete_one({"_id": existing_user.id})
    
    user = await user_service.create_user(user_data)
    
    # Make user an admin
    users_collection = await get_collection("users")
    await users_collection.update_one(
        {"_id": user.id},
        {"$set": {"is_admin": True}}
    )
    
    # Get updated user
    user_dict = await users_collection.find_one({"_id": user.id})
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