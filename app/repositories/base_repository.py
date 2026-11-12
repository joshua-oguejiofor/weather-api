"""This Base file contains basic operations for service layer """

from typing import Generic, TypeVar, Optional, Type
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Base

ModelType= TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):# set to acept two arguments
        self.model= model #dependency injection for model
        self.db= db #dependency injection for database
    
    
   
    async def get_by_model_id(self, id: int) -> Optional[ModelType]:
        return await self.db.get(self.model, id)
    
    

    async def create_object(self, obj: ModelType) -> ModelType:        
        self.db.add(obj)
        await self.db.flush()
        await self.db.refresh(obj)
        return obj


    async def update_object(self, obj: ModelType) -> ModelType:
        await self.db.flush()
        await self.db.refresh(obj)
        return obj


    async def delete_object(self, obj: ModelType) -> None:
        await self.db.delete(obj)
        await self.db.flush()

