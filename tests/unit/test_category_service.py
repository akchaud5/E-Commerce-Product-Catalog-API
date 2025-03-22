import pytest
from bson import ObjectId
from datetime import datetime

from app.models.category import CategoryCreate, CategoryUpdate
from app.services import category_service
from app.db.mongodb import get_categories_collection


@pytest.mark.asyncio
async def test_create_category():
    # Arrange
    category_data = CategoryCreate(
        name="Test Category Create",
        description="A category for testing create functionality"
    )
    
    # First delete the category if it exists
    categories_collection = await get_categories_collection()
    await categories_collection.delete_many({"name": category_data.name})
    
    # Act
    category = await category_service.create_category(category_data)
    
    # Assert
    assert category is not None
    assert category.name == category_data.name
    assert category.description == category_data.description
    assert hasattr(category, 'id')
    assert hasattr(category, 'created_at')
    assert hasattr(category, 'updated_at')


@pytest.mark.asyncio
async def test_get_category_by_id():
    # Arrange
    category_data = CategoryCreate(
        name="Category for Get By ID",
        description="A category for testing get by ID"
    )
    
    # First delete the category if it exists
    categories_collection = await get_categories_collection()
    await categories_collection.delete_many({"name": category_data.name})
    
    # Create a category
    created_category = await category_service.create_category(category_data)
    
    # Convert to string explicitly
    category_id = str(created_category.id)
    
    # Act - Get the category by ID
    category = await category_service.get_category_by_id(category_id)
    
    # Assert
    assert category is not None, f"Could not find category with ID: {category_id}"
    assert category.name == category_data.name
    assert category.description == category_data.description
    
    # Test non-existent category
    non_existent_category = await category_service.get_category_by_id("000000000000000000000000")
    assert non_existent_category is None


@pytest.mark.asyncio
async def test_get_category_by_name():
    # Arrange
    category_name = "Category for Get By Name"
    category_data = CategoryCreate(
        name=category_name,
        description="A category for testing get by name"
    )
    
    # First delete the category if it exists
    categories_collection = await get_categories_collection()
    await categories_collection.delete_many({"name": category_data.name})
    
    created_category = await category_service.create_category(category_data)
    
    # Act
    category = await category_service.get_category_by_name(category_name)
    
    # Assert
    assert category is not None
    assert category.name == category_name
    assert category.description == category_data.description
    
    # Test non-existent category
    non_existent_category = await category_service.get_category_by_name("Non-existent Category")
    assert non_existent_category is None


@pytest.mark.asyncio
async def test_update_category():
    # Arrange
    category_data = CategoryCreate(
        name="Category for Update",
        description="A category for testing update"
    )
    
    # First delete the category if it exists
    categories_collection = await get_categories_collection()
    await categories_collection.delete_many({"name": category_data.name})
    
    created_category = await category_service.create_category(category_data)
    
    # Update data
    new_name = "Updated Category Name"
    new_description = "Updated category description"
    update_data = {"name": new_name, "description": new_description}
    
    # Act
    updated_category = await category_service.update_category(str(created_category.id), update_data)
    
    # Assert
    assert updated_category is not None
    assert updated_category.name == new_name
    assert updated_category.description == new_description
    
    # Partial update
    partial_update = {"description": "Partially updated description"}
    
    # Act
    partially_updated_category = await category_service.update_category(
        str(created_category.id), partial_update
    )
    
    # Assert
    assert partially_updated_category is not None
    assert partially_updated_category.name == new_name  # Should remain unchanged
    assert partially_updated_category.description == "Partially updated description"


@pytest.mark.asyncio
async def test_delete_category():
    # Arrange
    category_data = CategoryCreate(
        name="Category for Delete",
        description="A category for testing delete"
    )
    
    # First delete the category if it exists
    categories_collection = await get_categories_collection()
    await categories_collection.delete_many({"name": category_data.name})
    
    created_category = await category_service.create_category(category_data)
    
    # Act
    result = await category_service.delete_category(str(created_category.id))
    
    # Assert
    assert result is True
    
    # Verify category no longer exists
    deleted_category = await category_service.get_category_by_id(str(created_category.id))
    assert deleted_category is None


@pytest.mark.asyncio
async def test_get_all_categories():
    # Arrange - Clear existing categories
    categories_collection = await get_categories_collection()
    await categories_collection.delete_many({})
    
    # Create multiple categories
    categories_data = [
        CategoryCreate(name="Electronics", description="Electronic devices and gadgets"),
        CategoryCreate(name="Clothing", description="Apparel and fashion items"),
        CategoryCreate(name="Books", description="Books and publications")
    ]
    
    for category_data in categories_data:
        await category_service.create_category(category_data)
    
    # Act
    categories = await category_service.get_all_categories()
    
    # Assert
    assert len(categories) >= 3
    
    # Verify names
    category_names = [category.name for category in categories]
    for data in categories_data:
        assert data.name in category_names
        
    # Test pagination
    limited_categories = await category_service.get_all_categories(limit=2)
    assert len(limited_categories) == 2
    
    skipped_categories = await category_service.get_all_categories(skip=1, limit=2)
    assert len(skipped_categories) == 2
    assert skipped_categories[0].name != categories[0].name