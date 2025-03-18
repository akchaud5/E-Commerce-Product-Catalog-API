from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional

from app.api.deps import get_current_user, get_current_active_user, get_current_admin_user
from app.services import product_service, category_service
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.models.user import UserInDB

router = APIRouter()

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_admin_user)])
async def create_product(product: ProductCreate):
    # Verify category exists
    category = await category_service.get_category_by_id(product.category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category not found"
        )
    
    # Create product
    created_product = await product_service.create_product(product)
    
    return {
        "id": str(created_product.id),
        "name": created_product.name,
        "description": created_product.description,
        "price": created_product.price,
        "stock": created_product.stock,
        "category_id": str(created_product.category_id),
        "is_active": created_product.is_active,
        "image_url": created_product.image_url,
        "tags": created_product.tags,
        "created_at": str(created_product.created_at),
        "updated_at": str(created_product.updated_at)
    }

@router.get("/", response_model=List[ProductResponse])
async def get_products(
    skip: int = 0, 
    limit: int = 100, 
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    category_id: Optional[str] = None,
    search: Optional[str] = None,
    active_only: bool = True
):
    # Handle search first if provided
    if search:
        products = await product_service.search_products(search, skip=skip, limit=limit)
    else:
        # Build filter params
        filter_params = {}
        
        if min_price is not None:
            filter_params["price"] = {"$gte": min_price}
        
        if max_price is not None:
            if "price" in filter_params:
                filter_params["price"]["$lte"] = max_price
            else:
                filter_params["price"] = {"$lte": max_price}
        
        if category_id:
            filter_params["category_id"] = category_id
            
        if active_only:
            filter_params["is_active"] = True
        
        products = await product_service.get_all_products(skip=skip, limit=limit, filter_params=filter_params)
    
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

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str):
    product = await product_service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return {
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
    }

@router.put("/{product_id}", response_model=ProductResponse, dependencies=[Depends(get_current_admin_user)])
async def update_product(product_id: str, product_update: ProductUpdate):
    # Check if product exists
    existing_product = await product_service.get_product_by_id(product_id)
    if not existing_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Verify category exists if being updated
    if product_update.category_id:
        category = await category_service.get_category_by_id(product_update.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found"
            )
    
    # Update product
    update_data = product_update.dict(exclude_unset=True)
    updated_product = await product_service.update_product(product_id, update_data)
    
    if not updated_product:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update product"
        )
    
    return {
        "id": str(updated_product.id),
        "name": updated_product.name,
        "description": updated_product.description,
        "price": updated_product.price,
        "stock": updated_product.stock,
        "category_id": str(updated_product.category_id),
        "is_active": updated_product.is_active,
        "image_url": updated_product.image_url,
        "tags": updated_product.tags,
        "created_at": str(updated_product.created_at),
        "updated_at": str(updated_product.updated_at)
    }

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_current_admin_user)])
async def delete_product(product_id: str):
    product = await product_service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    deleted = await product_service.delete_product(product_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete product"
        )
