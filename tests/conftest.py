import asyncio
import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.testclient import TestClient
from typing import Generator, Any
from bson import ObjectId

from app.main import app
from app.core.config import settings
from app.db.mongodb import database, get_collection
from app.services import user_service
from app.models.user import UserCreate


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_client() -> Generator[TestClient, Any, None]:
    """
    Create a FastAPI TestClient that uses the test database.
    """
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session", autouse=True)
async def setup_test_db():
    """
    Create test database and collections, and clean up after tests.
    """
    # Use a test database with a different name
    test_db_name = "ecommerce_test"
    test_mongodb_url = f"{settings.MONGODB_URL.rsplit('/', 1)[0]}/{test_db_name}"
    
    # Connect to test database
    client = AsyncIOMotorClient(test_mongodb_url)
    test_db = client[test_db_name]
    
    # Save original database
    original_database = database
    
    # Replace database with test database
    globals()["database"] = test_db
    
    # Create collections
    await test_db.create_collection("users")
    await test_db.create_collection("products")
    await test_db.create_collection("categories")
    
    yield
    
    # Clean up: drop test database
    await client.drop_database(test_db_name)
    
    # Restore original database
    globals()["database"] = original_database


@pytest.fixture
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


@pytest.fixture
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


@pytest.fixture
async def auth_headers(sample_user):
    """
    Create auth headers for testing.
    """
    from app.core.security import create_access_token
    
    access_token = create_access_token(subject=str(sample_user.id))
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
async def admin_auth_headers(admin_user):
    """
    Create admin auth headers for testing.
    """
    from app.core.security import create_access_token
    
    access_token = create_access_token(subject=str(admin_user["_id"]))
    return {"Authorization": f"Bearer {access_token}"}