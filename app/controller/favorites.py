
from fastapi import APIRouter, Depends

from app.models.user import User
from app.schemas import favorite
from app.services.favorites_service import FavoritesService
from app.utils.dependencies import get_current_user, get_favorites_service

router= APIRouter() 



"""Save a city to favorites."""
@router.post("/", status_code= 201)
async def add_favorite(
    data: favorite.FavoriteCityCreate,
    current_user: User= Depends(get_current_user),
    service: FavoritesService= Depends(get_favorites_service)
):
    await service.add_favorite(current_user.id, data)
    return{"msg": f"{data.city_name} added to favorites,"}




"""List all saved favorite cities for the current user."""
@router.get("/", status_code= 200, response_model= list[favorite.FavoriteCityResponse])
async def list_favorites(
    current_user: User= Depends(get_current_user),
    service: FavoritesService= Depends(get_favorites_service)
): 
    return await service.get_favorites(current_user.id)


"""Set a favorite city as the default city."""
@router.put("/{fav_id}/default", status_code= 200)
async def set_default_city(
    fav_id: int,
    current_user: User= Depends(get_current_user),
    service: FavoritesService= Depends(get_favorites_service)
):
    
    return await service.set_default(current_user.id, fav_id)


"""Fetch current weather for a specific saved favorite city."""
@router.get("/{fav_id}/weather", status_code= 200, response_model= favorite.CurrentWeatherResponse)
async def get_favorite_weather(
    fav_id: int,
    current_user: User= Depends(get_current_user),
    service: FavoritesService= Depends(get_favorites_service)
):
    return await service.get_weather_for_favorite(fav_id, current_user)
    
    

"""Remove a city from favorites."""
@router.delete("/{fav_id}", status_code= 204)
async def remove_favorite(
    fav_id: int,
    current_user: User= Depends(get_current_user),
    service: FavoritesService= Depends(get_favorites_service)
):
    
    return await service.remove_favorite(current_user= current_user, fav_id= fav_id)
