import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
import json
from app.main import app


@pytest.mark.asyncio
async def test_register_user():
    # Arrange
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Act
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "integration_test@example.com",
                "username": "integration_test_user",
                "password": "password123"
            }
        )
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "integration_test@example.com"
        assert data["username"] == "integration_test_user"
        assert "id" in data
        assert "is_active" in data
        assert "is_admin" in data


@pytest.mark.asyncio
async def test_register_existing_email():
    # Arrange
    async with AsyncClient(app=app, base_url="http://test") as client:
        # First create a user
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate_email@example.com",
                "username": "unique_username",
                "password": "password123"
            }
        )
        
        # Act - Try to register with the same email
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate_email@example.com",
                "username": "another_username",
                "password": "password123"
            }
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Email already registered" in data["detail"]


@pytest.mark.asyncio
async def test_register_existing_username():
    # Arrange
    async with AsyncClient(app=app, base_url="http://test") as client:
        # First create a user
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "unique_email@example.com",
                "username": "duplicate_username",
                "password": "password123"
            }
        )
        
        # Act - Try to register with the same username
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "another_email@example.com",
                "username": "duplicate_username",
                "password": "password123"
            }
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Username already taken" in data["detail"]


@pytest.mark.asyncio
async def test_login():
    # Arrange
    email = "login_test@example.com"
    username = "login_test_user"
    password = "password123"
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create a user
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "username": username,
                "password": password
            }
        )
        
        # Act - Login with correct credentials
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": password}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        
        # Act - Login with incorrect password
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": "wrong_password"}
        )
        
        # Assert
        assert response.status_code == 401