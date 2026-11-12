from fastapi import APIRouter, Depends

from app.models.user import User
from app.schemas.history import SearchHistoryResponse
from app.services.history_service import HistoryService
from app.utils.dependencies import get_current_user, get_history_service

router= APIRouter()


"""Get paginated weather search history for the current user."""
@router.get("/", status_code= 200, response_model= list[SearchHistoryResponse])
async def get_search_history(
    offset: int= 0,
    limit: int= 20,
    current_user: User= Depends(get_current_user),
    service: HistoryService= Depends(get_history_service)
):
    
    return await service.get_history(current_user= current_user, offset= offset, limit= limit)


"""Clear all search history for the current user."""
@router.delete("/", status_code= 200)
async def clear_search_history(
    current_user: User= Depends(get_current_user),
    service: HistoryService= Depends(get_history_service)
):
    
    await service.clear_history(current_user.id)
    return {"message": "Search history cleared"}
