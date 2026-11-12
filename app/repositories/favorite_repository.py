from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.favorite import FavoriteCity
from .base_repository import BaseRepository




class FavoriteCityRepository(BaseRepository[FavoriteCity]):
    def __init__(self, db: AsyncSession):
        super().__init__(FavoriteCity, db)



    async def count_user_favorites(self, user_id) -> int:
        result = await self.db.execute(
            select(func.count(FavoriteCity.id))
            .where(FavoriteCity.user_id == user_id)
        )
        return result.scalar_one()


    async def get_user_favorites(self, user_id) -> list[FavoriteCity]:
        result = await self.db.execute(
            select(FavoriteCity)
            .where(FavoriteCity.user_id == user_id)
            )
        return list(result.scalars().all())



    async def get_by_id(self, fav_id, user_id) -> Optional[FavoriteCity]:
        result = await self.db.execute(
            select(FavoriteCity)
            .where(
                FavoriteCity.id == fav_id, 
                FavoriteCity.user_id == user_id)
        )
        return result.scalar_one_or_none()

    