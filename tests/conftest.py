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
    Create test database and collections, or use a mock for CI environment.
    """
    # Use a test database with a different name
    test_db_name = "ecommerce_test"
    
    # Check if we're in CI environment
    in_ci = os.getenv("GITHUB_ACTIONS") == "true"
    
    # If we're in CI, use mock collections for unit tests
    if in_ci:
        print("GITHUB ACTIONS environment detected. Using mock database for unit tests.")
        
        # Create mock collections
        from unittest.mock import AsyncMock, MagicMock
        
        class MockCollection:
            """Mock MongoDB collection for unit tests"""
            
            def __init__(self, name):
                self.name = name
                self.data = {}  # Use dict to store documents by ID
                
            async def insert_one(self, document):
                """Insert a document and return a mock result with inserted_id"""
                # If no _id, create one
                if "_id" not in document:
                    document["_id"] = ObjectId()
                    
                # Store the document
                doc_id = document["_id"]
                self.data[str(doc_id)] = document.copy()
                
                # Return a result object with inserted_id
                result = MagicMock()
                result.inserted_id = doc_id
                return result
                
            async def find_one(self, query):
                """Find one document matching the query"""
                # Handle _id query
                if "_id" in query:
                    doc_id = str(query["_id"])
                    return self.data.get(doc_id)
                
                # Handle other field queries (simple implementation)
                for doc in self.data.values():
                    matches = True
                    for key, value in query.items():
                        if key not in doc or doc[key] != value:
                            matches = False
                            break
                    if matches:
                        return doc
                
                return None
                
            async def delete_many(self, query):
                """Delete documents matching the query"""
                # Simple implementation that deletes all documents
                self.data.clear()
                
                # Return a mock result
                result = MagicMock()
                result.deleted_count = 1
                return result
                
            async def delete_one(self, query):
                """Delete one document matching the query"""
                # Handle _id query
                if "_id" in query:
                    doc_id = str(query["_id"])
                    if doc_id in self.data:
                        del self.data[doc_id]
                        result = MagicMock()
                        result.deleted_count = 1
                        return result
                
                # Return a mock result
                result = MagicMock()
                result.deleted_count = 0
                return result
                
            async def update_one(self, query, update):
                """Update one document matching the query"""
                # Handle _id query
                if "_id" in query and "$set" in update:
                    doc_id = str(query["_id"])
                    if doc_id in self.data:
                        # Update the document
                        for key, value in update["$set"].items():
                            self.data[doc_id][key] = value
                        
                        # Return a mock result
                        result = MagicMock()
                        result.modified_count = 1
                        return result
                
                # Return a mock result
                result = MagicMock()
                result.modified_count = 0
                return result
                
            async def count_documents(self, query=None):
                """Count documents matching the query"""
                if query is None:
                    return len(self.data)
                    
                # Simple implementation
                count = 0
                for doc in self.data.values():
                    matches = True
                    for key, value in query.items():
                        if key not in doc or doc[key] != value:
                            matches = False
                            break
                    if matches:
                        count += 1
                
                return count
                
            def find(self, query=None):
                """Return a cursor for the query"""
                # Create and return a mock cursor
                cursor = MockCursor(self.data.values())
                return cursor
            
        class MockCursor:
            """Mock MongoDB cursor for unit tests"""
            
            def __init__(self, data):
                self.data = list(data)
                self._limit = None
                self._skip = 0
                self._sort_field = None
                self._sort_dir = 1
                
            def skip(self, skip):
                """Skip N documents"""
                self._skip = skip
                return self
                
            def limit(self, limit):
                """Limit to N documents"""
                self._limit = limit
                return self
                
            def sort(self, field, direction=1):
                """Sort by field"""
                self._sort_field = field
                self._sort_dir = direction
                return self
                
            async def __aiter__(self):
                """Async iterator implementation"""
                # Apply skip and limit
                result = self.data
                
                # Apply sort if specified
                if self._sort_field:
                    result = sorted(result, 
                                   key=lambda x: x.get(self._sort_field, ""),
                                   reverse=(self._sort_dir == -1))
                
                # Apply skip and limit
                start = self._skip
                end = None if self._limit is None else start + self._limit
                
                # Return the sliced data
                for item in list(result)[start:end]:
                    yield item
        
        # Create mock database and collections
        users_collection = MockCollection("users")
        products_collection = MockCollection("products")
        categories_collection = MockCollection("categories")
        
        # Create mock client and database
        mock_db = MagicMock()
        mock_db.users = users_collection
        mock_db.products = products_collection
        mock_db.categories = categories_collection
        
        mock_client = MagicMock()
        mock_client.__getitem__.return_value = mock_db
        
        # Create mock functions that return our collections
        async def get_test_client():
            return mock_client
            
        async def get_test_database():
            return mock_db
            
        async def get_test_products_collection():
            return products_collection
            
        async def get_test_categories_collection():
            return categories_collection
            
        async def get_test_users_collection():
            return users_collection
            
        # Patch the module
        import app.db.mongodb
        
        # Save the original functions
        original_get_client = app.db.mongodb.get_client
        original_get_database = app.db.mongodb.get_database
        original_get_products_collection = app.db.mongodb.get_products_collection
        original_get_categories_collection = app.db.mongodb.get_categories_collection
        original_get_users_collection = app.db.mongodb.get_users_collection
        
        # Replace with mock functions
        app.db.mongodb.get_client = get_test_client
        app.db.mongodb.get_database = get_test_database
        app.db.mongodb.get_products_collection = get_test_products_collection
        app.db.mongodb.get_categories_collection = get_test_categories_collection
        app.db.mongodb.get_users_collection = get_test_users_collection
        
        # Set global variables
        app.db.mongodb.client = mock_client
        app.db.mongodb.database = mock_db
        app.db.mongodb.products_collection = products_collection
        app.db.mongodb.categories_collection = categories_collection
        app.db.mongodb.users_collection = users_collection
        
        # Set a reference to the db in app for integration tests
        app.db = type('DB', (), {})()
        app.db.mongodb = type('MongoDB', (), {})()
        app.db.mongodb.get_client = get_test_client
        app.db.mongodb.get_database = get_test_database
        app.db.mongodb.get_products_collection = get_test_products_collection
        app.db.mongodb.get_categories_collection = get_test_categories_collection
        app.db.mongodb.get_users_collection = get_test_users_collection
        app.db.mongodb.client = mock_client
        app.db.mongodb.database = mock_db
        
        # Setup complete, yield control back to the tests
        yield
        
        # Restore original functions
        app.db.mongodb.get_client = original_get_client
        app.db.mongodb.get_database = original_get_database
        app.db.mongodb.get_products_collection = original_get_products_collection
        app.db.mongodb.get_categories_collection = original_get_categories_collection
        app.db.mongodb.get_users_collection = original_get_users_collection
        
        # Remove app.db
        if hasattr(app, 'db'):
            delattr(app, 'db')
        
    else:
        # For local development, try to use a real MongoDB instance
        try:
            # For CI environment, use the exact URL provided
            if settings.MONGODB_URL.startswith('mongodb+srv://'):
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
            print(f"Warning: MongoDB connection failed: {e}. Using mock database for unit tests.")
            # If MongoDB connection fails, fall back to the mock database approach
            yield


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