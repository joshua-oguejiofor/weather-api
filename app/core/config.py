from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config= SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )
    
    PROJECT_NAME: str= "Weather API"
    VERSION: str= "1.0.0"
    DEBUG: bool= False

    TEST_DATABASE_URL: str
    TEST_REDIS_URL: str
    DATABASE_URL: str
    REDIS_URL: str

    SECRET_KEY: SecretStr # Hides the value of the secret key in logs and error messages
    ALGORITHM: str= "HS256"
    
    #Admin
    ADMIN_EMAIL: str
    ADMIN_FIRST_NAME: str
    ADMIN_LAST_NAME: str
    ADMIN_PASSWORD: SecretStr
    

    #Token TTL
    EMAIL_VERIFICATION_EXPIRE_HOURS: int= 1
    ACCESS_TOKEN_EXPIRE_MINUTES: int= 15
    REFRESH_TOKEN_EXPIRE_DAYS: int= 7
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int= 10

    #Weather
    WEATHERAPI_KEY: SecretStr
    OPENWEATHERMAP_API_KEY: SecretStr
    WEATHER_PROVIDER: str= "openweathermap" 
    WEATHER_CACHE_TTL: int= 600

    #Email
    SMTP_HOST: str= "smtp.gmail.com"
    SMTP_PORT: int= 587
    SMTP_USER: str
    SMTP_PASSWORD: SecretStr
    EMAILS_FROM: str = "Weather App"

    ALLOWED_ORIGINS: list[str]= ["http://localhost:5501", "http://127.0.0.1:5501"]
    ALLOWED_HOSTS: list[str]= ["*"] 


   
               
# This function is used to cache the settings object so that it is only created once and reused throughout the application. 
# This improves performance and ensures consistency in configuration values.
@lru_cache
def get_settings():
    return Settings()


settings = get_settings()

