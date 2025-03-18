from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.api.deps import get_current_user, get_current_active_user, get_current_admin_user
from app.services import user_service
from app.schemas.user import UserResponse, UserUpdate
from app.models.user import UserInDB

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def read_user_me(current_user: UserInDB = Depends(get_current_active_user)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "username": current_user.username,
        "is_active": current_user.is_active,
        "is_admin": current_user.is_admin
    }

@router.put("/me", response_model=UserResponse)
async def update_user_me(user_update: UserUpdate, current_user: UserInDB = Depends(get_current_active_user)):
    # Check if user is trying to change email and if it's already taken
    if user_update.email and user_update.email != current_user.email:
        existing_user = await user_service.get_user_by_email(user_update.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Check if user is trying to change username and if it's already taken
    if user_update.username and user_update.username != current_user.username:
        existing_user = await user_service.get_user_by_username(user_update.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    # Update user
    update_data = user_update.dict(exclude_unset=True)
    updated_user = await user_service.update_user(str(current_user.id), update_data)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )
    
    return {
        "id": str(updated_user.id),
        "email": updated_user.email,
        "username": updated_user.username,
        "is_active": updated_user.is_active,
        "is_admin": updated_user.is_admin
    }

# Admin only routes
@router.get("/", response_model=List[UserResponse], dependencies=[Depends(get_current_admin_user)])
async def read_users(skip: int = 0, limit: int = 100):
    users = await user_service.get_all_users(skip=skip, limit=limit)
    return [
        {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "is_active": user.is_active,
            "is_admin": user.is_admin
        } for user in users
    ]

@router.get("/{user_id}", response_model=UserResponse, dependencies=[Depends(get_current_admin_user)])
async def read_user(user_id: str):
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "is_active": user.is_active,
        "is_admin": user.is_admin
    }
