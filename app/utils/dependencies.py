import logging

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis_server import is_token_blacklisted
from app.core.security import decode_token
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services import auth_service

oauth2_scheme= OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

logger= logging.getLogger(__name__)


async def get_current_user(token: str= Depends(oauth2_scheme), db: AsyncSession= Depends(get_db)) -> User:
    
    credentials_exception= HTTPException(
        status_code= 401,
        detail= "Could not validate credentials",
        headers= {"WWW-Authenticate": "Bearer"},
    )
    
    if await is_token_blacklisted(token):
        raise credentials_exception

    payload= decode_token(token)
    if not payload or payload.get("type") != "access":
        logger.warning("Invalid token used")
        raise credentials_exception

    user_id= payload.get("sub")
    repo= UserRepository(db)
    
    user= await repo.get_by_model_id(user_id)
    
    if not user or not user.is_active:
        logger.warning("Invalid user tried accessing")
        raise credentials_exception
    
    return user



"""Dependency Injections"""
from app.repositories import favorite_repository, history_repository
from app.services import (
    favorites_service,
    history_service,
    user_service,
    weather_service,
)


def get_history_service(db: AsyncSession= Depends(get_db)):
    history_repo= history_repository.SearchHistoryRepository(db)
    return history_service.HistoryService(history_repo)


def get_auth_service(db: AsyncSession= Depends(get_db)):
    user_repo= UserRepository(db)
    return auth_service.AuthService(user_repo)


def get_user_service(db: AsyncSession= Depends(get_db)):
    user_repo= UserRepository(db)
    return user_service.UserService(user_repo)

def get_weather_service(db: AsyncSession= Depends(get_db)):
    history_service= get_history_service(db)
    return weather_service.WeatherService(history_service= history_service)


def get_favorites_service(db: AsyncSession= Depends(get_db)):
    favorite_repo= favorite_repository.FavoriteCityRepository(db)
    weather_serv= get_weather_service(db)
    return favorites_service.FavoritesService(favorite_repo= favorite_repo, weather_service= weather_serv)
