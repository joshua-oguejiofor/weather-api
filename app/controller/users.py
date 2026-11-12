from fastapi import APIRouter, Depends

from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.services.user_service import UserService
from app.utils.dependencies import get_current_user, get_user_service

router= APIRouter()



"""Get the current authenticated user's profile."""
@router.get("/me", response_model= UserResponse, status_code= 200)
async def get_profile(current_user: User= Depends(get_current_user)):
    
    return current_user



"""Update profile info including preferred temperature unit (metric/imperial)."""    
@router.put("/me", status_code= 200)
async def update_profile(
    data: UserUpdate,
    current_user: User= Depends(get_current_user),
    service: UserService= Depends(get_user_service),
):
    await service.update_user(current_user= current_user, data= data)
    return {"msg": "Profile updated successfully."}



"""Deactivate the current user's account."""
@router.delete("/me", status_code= 200)
async def deactivate_account(
    current_user: User= Depends(get_current_user),
    service: UserService= Depends(get_user_service),
):
    
    await service.deactivate_account(current_user)
    return {"msg": "Account deactivated"}
