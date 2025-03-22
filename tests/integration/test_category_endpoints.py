import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
import json
from app.main import app


@pytest.fixture
async def sample_category_id(admin_auth_headers, async_client):
    """
    Create a sample category and return its ID.
    """
    response = await async_client.post(
        "/api/v1/categories/",
        headers=admin_auth_headers,
        json={
            "name": "Test Integration Category",
            "description": "A category for integration testing"
        }
    )
    
    data = response.json()
    return data["id"]


@pytest.mark.asyncio
async def test_create_category(admin_auth_headers, async_client):
    # Act
    response = await async_client.post(
        "/api/v1/categories/",
        headers=admin_auth_headers,
        json={
            "name": "New Integration Category",
            "description": "A new category created during integration testing"
        }
    )
    
    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Integration Category"
    assert data["description"] == "A new category created during integration testing"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_duplicate_category(admin_auth_headers):
    # Arrange
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create a category
        await client.post(
            "/api/v1/categories/",
            headers=admin_auth_headers,
            json={
                "name": "Duplicate Category",
                "description": "A category that will be duplicated"
            }
        )
        
        # Act - Try to create category with the same name
        response = await client.post(
            "/api/v1/categories/",
            headers=admin_auth_headers,
            json={
                "name": "Duplicate Category",
                "description": "Another description"
            }
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Category with this name already exists" in data["detail"]


@pytest.mark.asyncio
async def test_get_all_categories():
    # Arrange
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Act
        response = await client.get("/api/v1/categories/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # At least one category should exist from previous tests
        assert len(data) > 0
        for category in data:
            assert "id" in category
            assert "name" in category
            assert "description" in category
            assert "created_at" in category
            assert "updated_at" in category


@pytest.mark.asyncio
async def test_get_category_by_id(sample_category_id):
    # Arrange
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Act
        response = await client.get(f"/api/v1/categories/{sample_category_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_category_id
        assert "name" in data
        assert "description" in data
        
        # Act - Non-existent category
        response = await client.get("/api/v1/categories/000000000000000000000000")
        
        # Assert
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_category(admin_auth_headers, sample_category_id):
    # Arrange
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Act - Update name and description
        response = await client.put(
            f"/api/v1/categories/{sample_category_id}",
            headers=admin_auth_headers,
            json={
                "name": "Updated Category Name",
                "description": "Updated category description"
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Category Name"
        assert data["description"] == "Updated category description"
        
        # Act - Partial update (only description)
        response = await client.put(
            f"/api/v1/categories/{sample_category_id}",
            headers=admin_auth_headers,
            json={
                "description": "Only the description is updated"
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Category Name"  # Name should remain the same
        assert data["description"] == "Only the description is updated"


@pytest.mark.asyncio
async def test_delete_category(admin_auth_headers):
    # Arrange - Create a category to delete
    async with AsyncClient(app=app, base_url="http://test") as client:
        create_response = await client.post(
            "/api/v1/categories/",
            headers=admin_auth_headers,
            json={
                "name": "Category To Delete",
                "description": "This category will be deleted"
            }
        )
        
        category_id = create_response.json()["id"]
        
        # Act
        response = await client.delete(
            f"/api/v1/categories/{category_id}",
            headers=admin_auth_headers
        )
        
        # Assert
        assert response.status_code == 204
        
        # Verify category no longer exists
        get_response = await client.get(f"/api/v1/categories/{category_id}")
        assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_get_products_by_category(admin_auth_headers, sample_category_id):
    # Arrange - Create products in the category
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create a product in the category
        await client.post(
            "/api/v1/products/",
            headers=admin_auth_headers,
            json={
                "name": "Product In Category",
                "description": "A product for testing category products endpoint",
                "price": 29.99,
                "stock": 100,
                "category_id": sample_category_id
            }
        )
        
        # Act
        response = await client.get(f"/api/v1/categories/{sample_category_id}/products")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        for product in data:
            assert product["category_id"] == sample_category_id


@pytest.mark.asyncio
async def test_non_admin_cannot_modify_categories(auth_headers):
    # Arrange
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Act - Try to create category as non-admin
        response = await client.post(
            "/api/v1/categories/",
            headers=auth_headers,
            json={
                "name": "Unauthorized Category",
                "description": "This should not be created"
            }
        )
        
        # Assert
        assert response.status_code == 403
        data = response.json()
        assert "Not enough permissions" in data["detail"]