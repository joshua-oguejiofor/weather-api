import logging
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError

from app.core.config import settings

logger= logging.getLogger(__name__)


password_context = PasswordHasher()




def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return password_context.verify( hashed_password, plain_password)
    except (VerificationError, VerifyMismatchError):
        return False

def generate_otp() -> str :
    code= str(secrets.token_hex(4))
    return code


def create_email_verification_token(data: dict) -> str:
    to_encode= data.copy()
    expire= datetime.now(UTC) + timedelta(hours= settings.EMAIL_VERIFICATION_EXPIRE_HOURS)
    
    to_encode.update({"exp": expire, "type": "verify_email"})
    return jwt.encode(
        to_encode, 
        settings.SECRET_KEY.get_secret_value(), 
        algorithm= settings.ALGORITHM
        )


def create_access_token(data: dict) -> str:
    to_encode= data.copy()
    expire= datetime.now(UTC) + timedelta(minutes= settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type":"access"})
    return jwt.encode(
        to_encode, 
        settings.SECRET_KEY.get_secret_value(), 
        algorithm= settings.ALGORITHM
        )


def create_password_reset_token(data: dict) -> str:
    to_encode= data.copy()
    expire= datetime.now(UTC) + timedelta(minutes= settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type":"password_reset"})
    return jwt.encode(
        to_encode, 
        settings.SECRET_KEY.get_secret_value(), 
        algorithm= settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode= data.copy()
    expire= datetime.now(UTC) + timedelta(days= settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(
        to_encode, 
        settings.SECRET_KEY.get_secret_value(), 
        algorithm= settings.ALGORITHM)
    
 
def decode_token(token: str) -> dict | None :
    try:
        payload= jwt.decode(token, settings.SECRET_KEY.get_secret_value(), algorithms= [settings.ALGORITHM])
    except jwt.ExpiredSignatureError as e:
        logger.error(f"Expired token: {e}")
        raise ValueError("Token has expired")
    
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {e}")
        raise ValueError("Invalid token")
    
    return payload







