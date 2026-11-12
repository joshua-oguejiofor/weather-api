import logging
import time
from datetime import UTC, datetime

from fastapi import HTTPException
from fastapi.responses import RedirectResponse

from app.celery_server import celery_tasks
from app.core import redis_server, security
from app.core.config import settings
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import TokenResponse, UserCreate

logger= logging.getLogger(__name__)




class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo= user_repo
        
        
    async def register(self, data: UserCreate) -> User:
        
        if await self.user_repo.get_by_email(data.email):
            raise HTTPException(status_code= 400, detail= "Email already registered")
        
        added_user= User(
            email= data.email,
            hashed_password= security.hash_password(data.password),
            first_name= data.first_name,
            last_name= data.last_name,
            preferred_unit= data.preferred_unit
        )
        await self.user_repo.create_object(added_user)

        token= security.create_email_verification_token({"sub": str(added_user.id)})

        celery_tasks.email_verify_token_task.delay(added_user.email, token, added_user.first_name)
        logger.info(f"User registered successfully: {added_user.email}, verification email sent.")
        return True


    async def resend_email(self, email: str):
        
        db_user= await self.user_repo.get_by_email(email)
        if not db_user:
            raise HTTPException(status_code= 404, detail= "User not found")
        
        if db_user.is_verified:
            raise HTTPException(status_code= 400, detail= "Email already verified.")
        
        token= security.create_email_verification_token({"sub": str(db_user.id)})
        celery_tasks.email_verify_token_task.delay(db_user.email, token, db_user.first_name)
        logger.info(f"Verification email resent to: {db_user.email}")
        return True
    
    async def email_verify_token(self, token: str) -> RedirectResponse:
            
        if await redis_server.is_token_blacklisted(token):
            return RedirectResponse(
                url= "http://localhost:3000/?msg=Session expired.", status_code= 302
            ) 
        try:
            payload= security.decode_token(token)
        except ValueError as e:
            logger.warning("Error occured: ", str(e))
            return RedirectResponse(
            url= f"http://localhost:3000/?msg={str(e)}", status_code= 302
        ) 
        
        if payload.get("type") != "verify_email":
            logger.warning(f"Invalid token type: {payload.get('type')}")
            return RedirectResponse(
            url= "http://localhost:3000/?msg=invalid-token-type", status_code= 302
        )
                
        user_id= int(payload.get("sub"))
        db_user= await self.user_repo.get_by_model_id(user_id)
        if not db_user:
            return RedirectResponse(
            url= "http://localhost:3000/?msg=user-not-found", status_code= 302
        )
            
        if db_user.is_verified:
            return RedirectResponse(url= "http://localhost:3000/?msg=user-already-verified", status_code= 302)
        
        remaining_time= max(payload.get("exp") - int(time.time()), 1)
    
        db_user.is_verified= True
        
        await self.user_repo.update_object(db_user)   
        await redis_server.invalidate_token(token, remaining_time)
        logger.info(f"Email verified successful for user {db_user.id}")   
        return RedirectResponse( url= "http://localhost:3000/?msg=success", status_code= 302)
            


    async def login(self, email: str, password: str) -> TokenResponse:
        
        if await redis_server.get_cache(f"lock:{email}"):
            logger.warning(f"Login attempts for email {email} exceeded limit. Account locked.")
            raise HTTPException(
                status_code= 403, 
                detail= "Account locked due to multiple failed login attempts. Please try again after 15 minutes.")
            
        user= await self.user_repo.get_by_email(email)
        
        if not user or not security.verify_password(password, user.hashed_password):
            logger.warning(f"Failed login attempts for: {email}")

            attempts= await redis_server.increment_cache(f"failed_login:{email}")# Autommically delete after 15 minutes
            if attempts >= 5:
                await redis_server.set_cache(key= f"lock:{email}", value= "locked", expire= 900) 
                
            raise HTTPException(status_code= 401, detail= "Invalid credentials")
        
        if not user.is_active:
            raise HTTPException(status_code= 403, detail= "Account deactivated")

        if not user.is_verified:
            raise HTTPException(status_code= 401, detail= "Please verify your email before logging in.")

        access_token= security.create_access_token({"sub": str(user.id)})
        refresh_token_str= security.create_refresh_token({"sub": str(user.id)})

        await redis_server.set_cache(
            key= f"refresh_token:{user.id}",
            value= refresh_token_str, 
            expire= settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60)
        
        celery_tasks.send_login_notification_task.delay(user.email, user.first_name, datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S"))
        return TokenResponse(access_token= access_token, refresh_token= refresh_token_str)



    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        
        payload= security.decode_token(refresh_token)
         
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(status_code= 401, detail= "Invalid token type")
        
        user_id= payload.get("sub")
    
        stored_refresh_token= await redis_server.get_cache(f"refresh_token:{user_id}")
        if not stored_refresh_token or stored_refresh_token != refresh_token:
            raise HTTPException(status_code= 401, detail= "Invalid refresh token")
        
        await redis_server.delete_cache(f"refresh:{user_id}")
        
        new_access_token= security.create_access_token({"sub": str(user_id), "role": payload.get("role")})
        new_refresh_token= security.create_refresh_token({"sub": str(user_id)})
        
        await redis_server.set_cache(
                key= f"refresh_token:{user_id}",
                value= new_refresh_token, 
                expire= settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60)
                
        return TokenResponse(access_token= new_access_token, refresh_token= new_refresh_token)


    
    async def change_password(self, old_password: str, new_password: str, user: User)-> bool:
       
        user= await self.user_repo.get_by_model_id(user.id)
        if not user:
            raise HTTPException(status_code= 404, detail= "User not found")
        
        if not security.verify_password(old_password, user.hashed_password):
            raise HTTPException(status_code= 400, detail= "Old password is invalid")    
        
        user.hashed_password= security.hash_password(new_password)
        await self.user_repo.update_object(user)
        logger.info(f"Password changed successfully for user {user.id}")
        return True
    
    
    
    async def forget_password(self, email: str) -> bool:

        user= await self.user_repo.get_by_email(email)  
        if not user:
            raise HTTPException(status_code= 404, detail= "Invalid email address")
        
        otp= security.generate_otp()
        await redis_server.set_cache(
            key= f"otp:{email}",
            value= otp,
            expire= 10 * 60
        )
        celery_tasks.send_otp_email_task.delay(email, otp)
        
        return True
    

    async def verify_otp(self, email: str, otp: str):
        
        stored_otp= await redis_server.get_cache(f"otp:{email}")
        if not stored_otp:
            raise HTTPException(status_code= 401, detail= "OTP expired")
        
        if stored_otp != otp:
            raise HTTPException(status_code= 401, detail= "Invalid OTP")
                
        reset_token= security.create_password_reset_token({"sub": email})
        await redis_server.delete_cache(f"otp:{email}")
        return {"reset_token": reset_token}
    

    async def reset_password(self, reset_token: str, new_password: str) -> bool:
        
        if await redis_server.is_token_blacklisted(reset_token):
            raise HTTPException(status_code= 401, detail= "Expired reset token")
        try:

                payload= security.decode_token(reset_token)
        except ValueError as e:
            raise HTTPException(status_code= 401, detail= str(e))
        
        email= payload.get("sub")

        db_user= await self.user_repo.get_by_email(email)
        db_user.hashed_password= security.hash_password(new_password)
        
        remaining_time= max(payload.get("exp") - int(time.time()), 1)
        
        await self.user_repo.update_object(db_user)
        await redis_server.invalidate_token(reset_token, remaining_time)
        logger.info(f"Password reset successful for user {db_user.id}")
        return True
    
    
    
    async def logout(self, access_token: str) -> bool:
            
        if await redis_server.is_token_blacklisted(access_token):
            raise HTTPException(status_code= 401, detail= "Token revoked")
        
        payload= security.decode_token(access_token)
        
        remaining_time= max(payload.get("exp") - int(time.time()), 1)
        user_id= payload.get("sub")
        
        # Blacklist access token
        await redis_server.invalidate_token(access_token, remaining_time)

        # Remove refresh token
        await redis_server.delete_cache(f"refresh_token:{user_id}")
        return True







    
    
 
    
    
    