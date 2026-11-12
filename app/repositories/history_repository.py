from sqlalchemy import select, delete
from app.models.history import SearchHistory
from .base_repository import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession


class SearchHistoryRepository(BaseRepository[SearchHistory]):
    def __init__(self, db: AsyncSession):
        super().__init__(SearchHistory, db)
        
        

    async def get_user_history(self, user_id, offset: int, limit: int) -> list[SearchHistory]:
        result = await self.db.execute(
            select(SearchHistory)
            .where(SearchHistory.user_id == user_id)
            .order_by(SearchHistory.searched_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()
    
    
    
    async def delete_user_history(self, user_id: int):
        return await self.db.execute(
            delete(SearchHistory)
            .where(SearchHistory.user_id == user_id)
        )
        