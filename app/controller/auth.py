from fastapi import APIRouter, Depends, Form, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import EmailStr

from app.middleware.rate_limit import limiter
from app.models.user import User
from app.schemas import user
from app.services.auth_service import AuthService
from app.utils.dependencies import get_auth_service, get_current_user

router= APIRouter()
oauth2_scheme= OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


"""Register new user account."""
@router.post("/register", status_code= 201)
async def register(
    data: user.UserCreate,
    service: AuthService= Depends(get_auth_service)
    ):

    await service.register(data)
    return {"msg": "Check your email to continue verification process."}


@router.post('/register/resend-email', status_code= 200)
@limiter.limit("5/minute")
async def resend_email(
    request: Request, 
    data: user.EmailVerification,
    service: AuthService= Depends(get_auth_service)):
    
    await service.resend_email(email= data.email)
    return {"msg": "Check your email to continue verification process."}
    



#User clicks the verification link which is eqivallent to a get request on the browser
#This is set to a get request to prevent "405 method not allowed"
@router.get('/verify-email')
@limiter.limit("5/minute")
async def verify_token(
    request: Request, 
    token: str, 
    service: AuthService= Depends(get_auth_service)):
    
    return await service.email_verify_token(token)


"""
Because of Oauth form, username will simulate email
"""
@router.post("/login", response_model= user.TokenResponse, status_code= 200)
@limiter.limit("5/minute")
async def login(
    request: Request,
    username: EmailStr= Form(...),
    password: str= Form(..., min_length= 8),
    service: AuthService= Depends(get_auth_service)
    ):  
    
    return await service.login(email= username, password= password)



"""Rotate refresh token and get a new access token."""
@router.post("/refresh", response_model= user.TokenResponse, status_code= 200)
async def refresh(
    data: user.RefreshTokenRequest, 
    service: AuthService= Depends(get_auth_service)):
    
    return await service.refresh_token(data.refresh_token)


@router.patch('/password', status_code= 200)
@limiter.limit("5/minute")
async def change_password(
    request: Request,
    data: user.ChangePassword,
    current_user: User= Depends(get_current_user), 
    service: AuthService= Depends(get_auth_service)):
    await service.change_password(data.old_password, data.new_password, user= current_user)
    return {"msg":"Password update successfull"}


@router.post('/forget-password', status_code= 200)
@limiter.limit("5/minute")
async def forget_password(
    request: Request, 
    data: user.EmailVerification, 
    service: AuthService= Depends(get_auth_service)):
     
    
    await service.forget_password(data.email)
    
    return {"msg": "If the account exists, an OTP has been sent"}


@router.post('/password-forget/resend-otp', status_code= 200)
@limiter.limit("5/minute")
async def resend_otp(
    request: Request, 
    data: user.EmailVerification, 
    service: AuthService= Depends(get_auth_service)):
     
    
    await service.forget_password(data.email)
    
    return {"msg": "If the account exists, an OTP has been sent"}


@router.post('/verify-otp', status_code= 200)
@limiter.limit("5/minute")
async def verify_otp(
    request: Request, 
    data: user.OTPVerify,
    service: AuthService= Depends(get_auth_service)):
    
    return await service.verify_otp(email= data.email, otp= data.otp)
    

@router.post("/reset-password")
@limiter.limit("5/minute")
async def reset_password(
    request: Request, 
    data: user.PasswordReset, 
    service: AuthService= Depends(get_auth_service)):

    await service.reset_password(reset_token= data.reset_token, new_password= data.new_password)
    
    return {"msg": "Password reset successfully"}


"""Logout and invalidate current tokens."""
@router.post("/logout", status_code=200)
async def logout(
    token: str = Depends(oauth2_scheme),
    service: AuthService= Depends(get_auth_service)
    ):
    
    await service.logout(token)
    return {"msg": "Logged out successfully"}

