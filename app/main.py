import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.admin.admin_reg import register_admin_user
from app.controller import auth, favorites, history, users, weather
from app.core.config import settings
from app.error_handler_server.error_handlers import handle_errors
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.rate_limit import setup_rate_limiter

logging.basicConfig(
    level= logging.INFO, 
    format= "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
    handlers= [
        logging.StreamHandler(sys.stdout)
    ])

logger= logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Weather API...")
    await register_admin_user()  # Call the function to register the admin user
    
    yield
    logger.info("Shutting down Weather API...")


app= FastAPI(
    title= settings.PROJECT_NAME,
    version= settings.VERSION,
    description= "Production-ready Weather Application API",
    docs_url= "/api/v1/docs",
    redoc_url= "/api/v1/redoc",
    openapi_url= "/api/v1/openapi.json",
    lifespan= lifespan,
    
)


setup_rate_limiter(app)

app.add_middleware(LoggingMiddleware)
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts= settings.ALLOWED_HOSTS
    )

app.add_middleware(
    CORSMiddleware, 
    allow_origins= settings.ALLOWED_ORIGINS, 
    allow_credentials= True, 
    allow_methods= ["*"], 
    allow_headers= ["*"]
    )

app.include_router(users.router, prefix= "/api/v1/users", tags= ["Users"])
app.include_router(weather.router, prefix= "/api/v1/weather", tags= ["Weather"])
app.include_router(auth.router, prefix= "/api/v1/auth", tags= ["Authentication"])
app.include_router(favorites.router, prefix= "/api/v1/favorites", tags= ["Favorites"])
app.include_router(history.router, prefix= "/api/v1/history", tags= ["Search History"])


#Error handlers
handle_errors(app)


@app.get("/api/v1/health", tags= ["Health"])
async def health_check():
    return {
        "status": "Healthy", 
        "version": settings.VERSION, 
        "service": settings.PROJECT_NAME
        }
