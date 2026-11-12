from pydantic import EmailStr, field_validator, Field
from .base import StripedSchema, LoweredStripedSchema
from datetime import datetime


class UserCreate(StripedSchema):
    email: EmailStr
    password: str= Field(..., min_length=8)
    first_name: str= Field(..., min_length=2)
    last_name: str= Field(..., min_length=2)
    preferred_unit: str= Field(..., pattern= "^(metric|imperial)$", description="Preferred temperature unit: 'metric' or 'imperial'.")


    @field_validator("email", "first_name", "last_name", "preferred_unit", mode="before")
    @classmethod
    def validate_fields(cls, v: str):
        return v.lower()


class UserLogin(StripedSchema):
    email: EmailStr
    password: str= Field(..., min_length=8)
    
    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, v: str):
        return v.lower()


class UserUpdate(LoweredStripedSchema):
    first_name: str
    last_name: str
    preferred_unit: str= Field(..., pattern= "^(metric|imperial)$", description="Preferred temperature unit: 'metric' or 'imperial'.")



class UserResponse(LoweredStripedSchema):
    id: int
    email: str
    first_name: str
    last_name: str
    preferred_unit: str
    is_active: bool
    is_verified: bool
    created_at: datetime


class TokenResponse(StripedSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(StripedSchema):
    refresh_token: str


class ChangePassword(StripedSchema):
    old_password: str= Field(..., min_length=8)
    new_password: str= Field(..., min_length=8)
    
    
class EmailVerification(StripedSchema):
    email: EmailStr 
    
    
class OTPVerify(StripedSchema):
    email: EmailStr
    otp: str
    
class PasswordReset(StripedSchema):
    reset_token: str
    new_password: str= Field(..., min_length=8)

