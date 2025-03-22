import pytest
import pytest_asyncio
from bson import ObjectId
from datetime import datetime

from app.models.user import UserCreate
from app.services import user_service
from app.db.mongodb import get_users_collection


@pytest.mark.asyncio
async def test_create_user():
    # Arrange
    user_data = UserCreate(
        email="test_create@example.com",
        username="test_create_user",
        password="password123"
    )
    
    # First delete the user if it exists
    users_collection = await get_users_collection()
    await users_collection.delete_many({"email": user_data.email})
    
    # Act
    user = await user_service.create_user(user_data)
    
    # Assert
    assert user is not None
    assert user.email == user_data.email
    assert user.username == user_data.username
    assert hasattr(user, 'hashed_password')
    assert user.hashed_password != user_data.password  # Password should be hashed


@pytest.mark.asyncio
async def test_get_user_by_email():
    # Arrange
    email = "test_email@example.com"
    username = "test_email_user"
    
    # Create a test user
    user_data = UserCreate(
        email=email,
        username=username,
        password="password123"
    )
    
    # First delete the user if it exists
    users_collection = await get_users_collection()
    await users_collection.delete_many({"email": email})
    
    created_user = await user_service.create_user(user_data)
    
    # Act
    user = await user_service.get_user_by_email(email)
    
    # Assert
    assert user is not None
    assert user.email == email
    assert user.username == username


@pytest.mark.asyncio
async def test_get_user_by_username():
    # Arrange
    email = "test_username@example.com"
    username = "test_username_user"
    
    # Create a test user
    user_data = UserCreate(
        email=email,
        username=username,
        password="password123"
    )
    
    # First delete the user if it exists
    users_collection = await get_users_collection()
    await users_collection.delete_many({"username": username})
    
    created_user = await user_service.create_user(user_data)
    
    # Act
    user = await user_service.get_user_by_username(username)
    
    # Assert
    assert user is not None
    assert user.email == email
    assert user.username == username


@pytest.mark.asyncio
async def test_authenticate_user():
    # Arrange
    email = "test_auth@example.com"
    username = "test_auth_user"
    password = "password123"
    
    # Create a test user
    user_data = UserCreate(
        email=email,
        username=username,
        password=password
    )
    
    # First delete the user if it exists
    users_collection = await get_users_collection()
    await users_collection.delete_many({"email": email})
    
    created_user = await user_service.create_user(user_data)
    
    # Act - Correct password
    authenticated_user = await user_service.authenticate_user(email, password)
    
    # Assert
    assert authenticated_user is not None
    assert authenticated_user.id == created_user.id
    
    # Act - Incorrect password
    authenticated_user = await user_service.authenticate_user(email, "wrong_password")
    
    # Assert
    assert authenticated_user is None


@pytest.mark.asyncio
async def test_update_user():
    # Arrange
    email = "test_update@example.com"
    username = "test_update_user"
    
    # Create a test user
    user_data = UserCreate(
        email=email,
        username=username,
        password="password123"
    )
    
    # First delete the user if it exists
    users_collection = await get_users_collection()
    await users_collection.delete_many({"email": email})
    
    created_user = await user_service.create_user(user_data)
    
    # Update data
    new_username = "updated_username"
    update_data = {"username": new_username}
    
    # Act
    updated_user = await user_service.update_user(str(created_user.id), update_data)
    
    # Assert
    assert updated_user is not None
    assert updated_user.username == new_username
    assert updated_user.email == email  # Email should not change
    
    # Test password update
    new_password = "new_password123"
    update_data = {"password": new_password}
    
    # Act
    updated_user = await user_service.update_user(str(created_user.id), update_data)
    
    # Assert
    assert updated_user is not None
    
    # Verify password change by authenticating
    authenticated_user = await user_service.authenticate_user(email, new_password)
    assert authenticated_user is not None