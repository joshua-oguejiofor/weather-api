from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserUpdate


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo= user_repo
        
        
    async def update_user(self, current_user: User, data: UserUpdate):
        
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(current_user, field, value)
                
        await self.user_repo.update_object(current_user)
        return True
    
      
        
    async def deactivate_account(self, current_user: User):
        
        current_user.is_active= False
        
        return await self.user_repo.update_object(current_user)
