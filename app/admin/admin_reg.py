"""
This modeule is responsible for registering an admin user in the database if it does not already exist. 
It checks for the existence of a user with the email specified in the settings and creates one with the provided password and role if not found.
"""


from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import User


async def register_admin_user():
    async with AsyncSessionLocal() as db:
    
        existing_user= await db.scalar(
            select(User)
            .where(User.email == settings.ADMIN_EMAIL)
            )
        
        if existing_user:
            return True
        
        admin_user= User(
            email= settings.ADMIN_EMAIL, 
            first_name= settings.ADMIN_FIRST_NAME,
            last_name= settings.ADMIN_LAST_NAME,
            hashed_password= hash_password(settings.ADMIN_PASSWORD.get_secret_value()),
            is_active= True, 
            is_verified= True, 
            role= "admin",
            preferred_unit= "imperial" 
            )
        
        db.add(admin_user) 
        await db.commit()
        await db.refresh(admin_user)
        return True
    
        
    