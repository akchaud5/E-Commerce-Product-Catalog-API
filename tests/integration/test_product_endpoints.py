import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
import json
from app.main import app


@pytest.fixture
async def sample_category_id(admin_auth_headers):
    """
    Create a sample category and return its ID.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/categories/",
            headers=admin_auth_headers,
            json={
                "name": "Product Test Category",
                "description": "A category for product integration testing"
            }
        )
        
        data = response.json()
        return data["id"]


@pytest.fixture
async def sample_product_id(admin_auth_headers, sample_category_id):
    """
    Create a sample product and return its ID.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/products/",
            headers=admin_auth_headers,
            json={
                "name": "Test Integration Product",
                "description": "A product for integration testing",
                "price": 29.99,
                "stock": 100,
                "category_id": sample_category_id,
                "tags": ["test", "integration"]
            }
        )
        
        data = response.json()
        return data["id"]


@pytest.mark.asyncio
async def test_create_product(admin_auth_headers, sample_category_id):
    # Arrange
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Act
        response = await client.post(
            "/api/v1/products/",
            headers=admin_auth_headers,
            json={
                "name": "New Integration Product",
                "description": "A new product created during integration testing",
                "price": 39.99,
                "stock": 50,
                "category_id": sample_category_id,
                "image_url": "https://example.com/image.jpg",
                "tags": ["new", "test"]
            }
        )
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Integration Product"
        assert data["description"] == "A new product created during integration testing"
        assert data["price"] == 39.99
        assert data["stock"] == 50
        assert data["category_id"] == sample_category_id
        assert data["image_url"] == "https://example.com/image.jpg"
        assert "test" in data["tags"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_product_invalid_category(admin_auth_headers):
    # Arrange
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Act - Try to create product with non-existent category
        response = await client.post(
            "/api/v1/products/",
            headers=admin_auth_headers,
            json={
                "name": "Invalid Category Product",
                "description": "A product with an invalid category",
                "price": 19.99,
                "stock": 30,
                "category_id": "000000000000000000000000"
            }
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Category not found" in data["detail"]


@pytest.mark.asyncio
async def test_get_all_products():
    # Arrange
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Act
        response = await client.get("/api/v1/products/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # At least one product should exist from previous tests
        assert len(data) > 0
        for product in data:
            assert "id" in product
            assert "name" in product
            assert "description" in product
            assert "price" in product
            assert "stock" in product
            assert "category_id" in product
            assert "created_at" in product
            assert "updated_at" in product


@pytest.mark.asyncio
async def test_get_products_with_filters(sample_category_id):
    # Arrange
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Act - Filter by category
        response = await client.get(f"/api/v1/products/?category_id={sample_category_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for product in data:
            assert product["category_id"] == sample_category_id
        
        # Act - Filter by price range
        response = await client.get("/api/v1/products/?min_price=25&max_price=50")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        for product in data:
            assert product["price"] >= 25
            assert product["price"] <= 50


@pytest.mark.asyncio
async def test_search_products():
    # Arrange
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Act - Search by name
        response = await client.get("/api/v1/products/?search=Integration")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        found_integration_product = False
        for product in data:
            if "Integration" in product["name"]:
                found_integration_product = True
                break
        assert found_integration_product


@pytest.mark.asyncio
async def test_get_product_by_id(sample_product_id):
    # Arrange
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Act
        response = await client.get(f"/api/v1/products/{sample_product_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_product_id
        
        # Act - Non-existent product
        response = await client.get("/api/v1/products/000000000000000000000000")
        
        # Assert
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_product(admin_auth_headers, sample_product_id, sample_category_id):
    # Arrange
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Act - Full update
        response = await client.put(
            f"/api/v1/products/{sample_product_id}",
            headers=admin_auth_headers,
            json={
                "name": "Updated Product Name",
                "description": "Updated product description",
                "price": 49.99,
                "stock": 200,
                "category_id": sample_category_id,
                "is_active": True,
                "tags": ["updated", "test"]
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Product Name"
        assert data["description"] == "Updated product description"
        assert data["price"] == 49.99
        assert data["stock"] == 200
        assert "updated" in data["tags"]
        
        # Act - Partial update (only price and stock)
        response = await client.put(
            f"/api/v1/products/{sample_product_id}",
            headers=admin_auth_headers,
            json={
                "price": 59.99,
                "stock": 150
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Product Name"  # Name should remain unchanged
        assert data["price"] == 59.99
        assert data["stock"] == 150


@pytest.mark.asyncio
async def test_delete_product(admin_auth_headers, sample_category_id):
    # Arrange - Create a product to delete
    async with AsyncClient(app=app, base_url="http://test") as client:
        create_response = await client.post(
            "/api/v1/products/",
            headers=admin_auth_headers,
            json={
                "name": "Product To Delete",
                "description": "This product will be deleted",
                "price": 9.99,
                "stock": 10,
                "category_id": sample_category_id
            }
        )
        
        product_id = create_response.json()["id"]
        
        # Act
        response = await client.delete(
            f"/api/v1/products/{product_id}",
            headers=admin_auth_headers
        )
        
        # Assert
        assert response.status_code == 204
        
        # Verify product no longer exists
        get_response = await client.get(f"/api/v1/products/{product_id}")
        assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_non_admin_cannot_modify_products(auth_headers, sample_category_id):
    # Arrange
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Act - Try to create product as non-admin
        response = await client.post(
            "/api/v1/products/",
            headers=auth_headers,
            json={
                "name": "Unauthorized Product",
                "description": "This should not be created",
                "price": 9.99,
                "stock": 10,
                "category_id": sample_category_id
            }
        )
        
        # Assert
        assert response.status_code == 403
        data = response.json()
        assert "Not enough permissions" in data["detail"]