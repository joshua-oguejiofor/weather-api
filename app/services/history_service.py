from app.models import history, user
from app.repositories.history_repository import SearchHistoryRepository


class HistoryService:
    def __init__(self, history_repo: SearchHistoryRepository):
        self.history_repo= history_repo

    async def record_search(
        self, user_id, 
        query: str, 
        query_type: str= "city",
        result_city: str= None, 
        result_country: str= None,
        weather_snapshot: dict= None,
        lat: float = None, 
        lon: float = None
        ) -> history.SearchHistory:
        
        
        entry = history.SearchHistory(
            user_id= user_id,
            query= query,
            query_type= query_type,
            result_city= result_city,
            result_country= result_country,
            weather_snapshot= weather_snapshot,
            latitude= lat,
            longitude= lon,
        )
        return await self.history_repo.create_object(entry)


    async def get_history(self, current_user: user.User, offset: int, limit: int) -> list[history.SearchHistory]:
        
        return await self.history_repo.get_user_history(
            user_id= current_user.id, 
            offset= offset, 
            limit= limit)


    async def clear_history(self, user_id: int) -> bool:
        await self.history_repo.delete_user_history(user_id)
        return True
