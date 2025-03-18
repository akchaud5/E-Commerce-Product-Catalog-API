import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
import json
from app.main import app


@pytest.mark.asyncio
async def test_read_user_me(auth_headers):
    # Arrange
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Act
        response = await client.get(
            "/api/v1/users/me",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "username" in data
        assert "is_active" in data
        assert "is_admin" in data


@pytest.mark.asyncio
async def test_update_user_me(auth_headers):
    # Arrange
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Act - Update username
        new_username = "updated_integration_username"
        response = await client.put(
            "/api/v1/users/me",
            headers=auth_headers,
            json={"username": new_username}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == new_username
        
        # Act - Update email
        new_email = "updated_integration@example.com"
        response = await client.put(
            "/api/v1/users/me",
            headers=auth_headers,
            json={"email": new_email}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == new_email


@pytest.mark.asyncio
async def test_update_user_me_existing_email(auth_headers):
    # Arrange
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create another user with a specific email
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "taken_email@example.com",
                "username": "another_user",
                "password": "password123"
            }
        )
        
        # Act - Try to update to an existing email
        response = await client.put(
            "/api/v1/users/me",
            headers=auth_headers,
            json={"email": "taken_email@example.com"}
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Email already registered" in data["detail"]


@pytest.mark.asyncio
async def test_admin_get_all_users(admin_auth_headers):
    # Arrange
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Act
        response = await client.get(
            "/api/v1/users/",
            headers=admin_auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        for user in data:
            assert "id" in user
            assert "email" in user
            assert "username" in user


@pytest.mark.asyncio
async def test_admin_get_user_by_id(admin_auth_headers, sample_user):
    # Arrange
    user_id = str(sample_user.id)
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Act
        response = await client.get(
            f"/api/v1/users/{user_id}",
            headers=admin_auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["email"] == sample_user.email
        assert data["username"] == sample_user.username
        
        # Act - Non-existent user
        response = await client.get(
            "/api/v1/users/000000000000000000000000",
            headers=admin_auth_headers
        )
        
        # Assert
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_non_admin_cannot_access_admin_routes(auth_headers):
    # Arrange
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Act - Try to access admin-only route
        response = await client.get(
            "/api/v1/users/",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 403
        data = response.json()
        assert "Not enough permissions" in data["detail"]