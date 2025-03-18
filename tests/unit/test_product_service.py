import pytest
import pytest_asyncio
from bson import ObjectId
from datetime import datetime

from app.models.product import ProductCreate, ProductUpdate
from app.models.category import CategoryCreate
from app.services import product_service, category_service
from app.db.mongodb import database


@pytest_asyncio.fixture
async def sample_category():
    """
    Create a sample category for testing.
    """
    category_data = CategoryCreate(
        name="Test Category",
        description="A category for testing products"
    )
    
    # Check if category already exists and delete it
    existing_category = await category_service.get_category_by_name(category_data.name)
    if existing_category:
        await database.categories.delete_one({"_id": existing_category.id})
    
    category = await category_service.create_category(category_data)
    return category


@pytest.mark.asyncio
async def test_create_product(sample_category):
    # Arrange
    product_data = ProductCreate(
        name="Test Product",
        description="A test product",
        price=29.99,
        stock=100,
        category_id=str(sample_category.id),
        is_active=True,
        tags=["test", "product"]
    )
    
    # Act
    product = await product_service.create_product(product_data)
    
    # Assert
    assert product is not None
    assert product.name == product_data.name
    assert product.description == product_data.description
    assert product.price == product_data.price
    assert product.stock == product_data.stock
    assert str(product.category_id) == str(sample_category.id)
    assert product.is_active == product_data.is_active
    assert product.tags == product_data.tags


@pytest.mark.asyncio
async def test_get_product_by_id(sample_category):
    # Arrange
    product_data = ProductCreate(
        name="Product for Get By ID",
        description="A product for testing get by ID",
        price=19.99,
        stock=50,
        category_id=str(sample_category.id),
        is_active=True
    )
    
    created_product = await product_service.create_product(product_data)
    
    # Act
    product = await product_service.get_product_by_id(str(created_product.id))
    
    # Assert
    assert product is not None
    assert str(product.id) == str(created_product.id)
    assert product.name == product_data.name
    assert product.description == product_data.description
    
    # Test non-existent product
    non_existent_product = await product_service.get_product_by_id("000000000000000000000000")
    assert non_existent_product is None


@pytest.mark.asyncio
async def test_update_product(sample_category):
    # Arrange
    product_data = ProductCreate(
        name="Product for Update",
        description="A product for testing update",
        price=39.99,
        stock=200,
        category_id=str(sample_category.id),
        is_active=True
    )
    
    created_product = await product_service.create_product(product_data)
    
    # Update data
    new_name = "Updated Product Name"
    new_price = 49.99
    update_data = {"name": new_name, "price": new_price}
    
    # Act
    updated_product = await product_service.update_product(str(created_product.id), update_data)
    
    # Assert
    assert updated_product is not None
    assert updated_product.name == new_name
    assert updated_product.price == new_price
    assert updated_product.description == product_data.description  # Should remain unchanged


@pytest.mark.asyncio
async def test_delete_product(sample_category):
    # Arrange
    product_data = ProductCreate(
        name="Product for Delete",
        description="A product for testing delete",
        price=9.99,
        stock=10,
        category_id=str(sample_category.id),
        is_active=True
    )
    
    created_product = await product_service.create_product(product_data)
    
    # Act
    result = await product_service.delete_product(str(created_product.id))
    
    # Assert
    assert result is True
    
    # Verify product no longer exists
    deleted_product = await product_service.get_product_by_id(str(created_product.id))
    assert deleted_product is None


@pytest.mark.asyncio
async def test_get_all_products(sample_category):
    # Arrange - Clear existing products
    await database.products.delete_many({})
    
    # Create multiple products
    product_data1 = ProductCreate(
        name="Product 1",
        description="First test product",
        price=19.99,
        stock=100,
        category_id=str(sample_category.id),
        is_active=True
    )
    
    product_data2 = ProductCreate(
        name="Product 2",
        description="Second test product",
        price=29.99,
        stock=200,
        category_id=str(sample_category.id),
        is_active=True
    )
    
    await product_service.create_product(product_data1)
    await product_service.create_product(product_data2)
    
    # Act
    products = await product_service.get_all_products()
    
    # Assert
    assert len(products) >= 2
    
    # Test with filter
    active_products = await product_service.get_all_products(filter_params={"is_active": True})
    assert len(active_products) >= 2
    
    # Test with price filter
    price_filtered_products = await product_service.get_all_products(
        filter_params={"price": {"$gte": 20.0}}
    )
    assert any(p.name == "Product 2" for p in price_filtered_products)
    assert not any(p.name == "Product 1" for p in price_filtered_products)


@pytest.mark.asyncio
async def test_search_products(sample_category):
    # Arrange - Clear existing products
    await database.products.delete_many({})
    
    # Create products with searchable terms
    product_data1 = ProductCreate(
        name="Smartphone X",
        description="A high-end smartphone with great features",
        price=699.99,
        stock=50,
        category_id=str(sample_category.id),
        tags=["electronics", "smartphone", "mobile"]
    )
    
    product_data2 = ProductCreate(
        name="Laptop Pro",
        description="Professional laptop for developers",
        price=1299.99,
        stock=30,
        category_id=str(sample_category.id),
        tags=["electronics", "computer", "laptop"]
    )
    
    await product_service.create_product(product_data1)
    await product_service.create_product(product_data2)
    
    # Act - Search by name
    smartphone_results = await product_service.search_products("Smartphone")
    
    # Assert
    assert len(smartphone_results) == 1
    assert smartphone_results[0].name == "Smartphone X"
    
    # Act - Search by description
    developer_results = await product_service.search_products("developer")
    
    # Assert
    assert len(developer_results) == 1
    assert developer_results[0].name == "Laptop Pro"
    
    # Act - Search by tag
    electronics_results = await product_service.search_products("electronics")
    
    # Assert
    assert len(electronics_results) >= 2


@pytest.mark.asyncio
async def test_get_products_by_category(sample_category):
    # Arrange - Clear existing products
    await database.products.delete_many({})
    
    # Create multiple products in the same category
    for i in range(3):
        product_data = ProductCreate(
            name=f"Category Product {i+1}",
            description=f"Product {i+1} in test category",
            price=10.99 * (i+1),
            stock=100 * (i+1),
            category_id=str(sample_category.id),
            is_active=True
        )
        await product_service.create_product(product_data)
    
    # Create a different category and product
    other_category = await category_service.create_category(
        CategoryCreate(name="Other Category", description="Another category")
    )
    
    other_product = ProductCreate(
        name="Other Product",
        description="Product in other category",
        price=99.99,
        stock=50,
        category_id=str(other_category.id),
        is_active=True
    )
    await product_service.create_product(other_product)
    
    # Act
    category_products = await product_service.get_products_by_category(str(sample_category.id))
    
    # Assert
    assert len(category_products) == 3
    for product in category_products:
        assert str(product.category_id) == str(sample_category.id)
    
    # Check other category
    other_category_products = await product_service.get_products_by_category(str(other_category.id))
    assert len(other_category_products) == 1
    assert other_category_products[0].name == "Other Product"