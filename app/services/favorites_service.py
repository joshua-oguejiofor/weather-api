from fastapi import HTTPException

from app.models.favorite import FavoriteCity
from app.models.user import User
from app.repositories.favorite_repository import FavoriteCityRepository
from app.schemas.favorite import FavoriteCityCreate
from app.services.weather_service import WeatherService


class FavoritesService:
    def __init__(
        self, favorite_repo: FavoriteCityRepository, 
        weather_service: WeatherService= None):
        self.favorite_repo= favorite_repo
        self.weather_service= weather_service



    async def add_favorite(self, user_id, data: FavoriteCityCreate) -> FavoriteCity:
        
        fav_count= await self.favorite_repo.count_user_favorites(user_id)
        if fav_count >= 10:
            raise HTTPException(status_code= 400, detail= "Maximum number of favorite cities reached (10)")
        
        existing = await self.favorite_repo.get_user_favorites(user_id)
        for fav in existing:
            if fav.city_name == data.city_name:
                raise HTTPException(status_code= 400, detail= "City already in favorites")

        if data.is_default:
            for fav in existing:
                fav.is_default= False

        city = FavoriteCity(
            user_id= user_id,
            city_name= data.city_name,
            country_code= data.country_code,
            latitude= data.latitude,
            longitude= data.longitude,
            is_default= data.is_default
        )
        return await self.favorite_repo.create_object(city)


    async def get_favorites(self, user_id) -> list[FavoriteCity]:
        return await self.favorite_repo.get_user_favorites(user_id)


    async def get_weather_for_favorite(self, fav_id: int, current_user: User) -> dict:
            
        favorites= await self.get_favorites(current_user.id)
        
        target= next((f for f in favorites if str(f.id) == str(fav_id)), None)
        if not target:
            raise HTTPException(status_code= 404, detail= "Favorite not found")

        return await self.weather_service.get_current_weather(target.city_name, current_user)



    async def set_default(self, user_id, fav_id) -> FavoriteCity:
        
        favorites= await self.favorite_repo.get_user_favorites(user_id)
        
        target = None
        for fav in favorites:
            fav.is_default= False
            if str(fav.id) == str(fav_id):
                target= fav
                
        if not target:
            raise HTTPException(status_code= 404, detail= "Favorite not found")
        
        target.is_default= True
        await self.favorite_repo.update_object(target)
        return target



    async def remove_favorite(self, current_user: User, fav_id: int) -> bool:
        
        fav= await self.favorite_repo.get_by_id(fav_id= fav_id, user_id= current_user.id)
        if not fav:
            raise HTTPException(status_code= 404, detail="Favorite not found")
        
        await self.favorite_repo.delete_object(fav)
        return True
