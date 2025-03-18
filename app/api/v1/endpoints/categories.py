from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.api.deps import get_current_user, get_current_active_user, get_current_admin_user
from app.services import category_service, product_service
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.schemas.product import ProductResponse
from app.models.user import UserInDB

router = APIRouter()

@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_admin_user)])
async def create_category(category: CategoryCreate):
    # Check if category with same name already exists
    existing_category = await category_service.get_category_by_name(category.name)
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this name already exists"
        )
    
    # Create category
    created_category = await category_service.create_category(category)
    
    return {
        "id": str(created_category.id),
        "name": created_category.name,
        "description": created_category.description,
        "created_at": str(created_category.created_at),
        "updated_at": str(created_category.updated_at)
    }

@router.get("/", response_model=List[CategoryResponse])
async def get_categories(skip: int = 0, limit: int = 100):
    categories = await category_service.get_all_categories(skip=skip, limit=limit)
    
    return [
        {
            "id": str(category.id),
            "name": category.name,
            "description": category.description,
            "created_at": str(category.created_at),
            "updated_at": str(category.updated_at)
        } for category in categories
    ]

@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: str):
    category = await category_service.get_category_by_id(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    return {
        "id": str(category.id),
        "name": category.name,
        "description": category.description,
        "created_at": str(category.created_at),
        "updated_at": str(category.updated_at)
    }

@router.put("/{category_id}", response_model=CategoryResponse, dependencies=[Depends(get_current_admin_user)])
async def update_category(category_id: str, category_update: CategoryUpdate):
    # Check if category exists
    existing_category = await category_service.get_category_by_id(category_id)
    if not existing_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Check if name is being updated and if it's already taken
    if category_update.name and category_update.name != existing_category.name:
        name_exists = await category_service.get_category_by_name(category_update.name)
        if name_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category with this name already exists"
            )
    
    # Update category
    update_data = category_update.dict(exclude_unset=True)
    updated_category = await category_service.update_category(category_id, update_data)
    
    if not updated_category:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update category"
        )
    
    return {
        "id": str(updated_category.id),
        "name": updated_category.name,
        "description": updated_category.description,
        "created_at": str(updated_category.created_at),
        "updated_at": str(updated_category.updated_at)
    }

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_current_admin_user)])
async def delete_category(category_id: str):
    # Check if category exists
    category = await category_service.get_category_by_id(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Check if category has products
    products = await product_service.get_products_by_category(category_id)
    if products:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category with existing products"
        )
    
    deleted = await category_service.delete_category(category_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete category"
        )

@router.get("/{category_id}/products", response_model=List[ProductResponse])
async def get_products_by_category(category_id: str, skip: int = 0, limit: int = 100):
    # Check if category exists
    category = await category_service.get_category_by_id(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    products = await product_service.get_products_by_category(category_id, skip=skip, limit=limit)
    
    return [
        {
            "id": str(product.id),
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "stock": product.stock,
            "category_id": str(product.category_id),
            "is_active": product.is_active,
            "image_url": product.image_url,
            "tags": product.tags,
            "created_at": str(product.created_at),
            "updated_at": str(product.updated_at)
        } for product in products
    ]
