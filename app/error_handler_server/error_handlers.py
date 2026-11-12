import logging

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

logger= logging.getLogger(__name__)


def handle_errors(app: FastAPI):
    @app.exception_handler(RateLimitExceeded)
    async def ratelimit_error_handler(request: Request, exc: RateLimitExceeded):
        logger.warning(f"Rate limit exceeded for client {request.client.host}: {exc.detail}")
        return JSONResponse(
            status_code=429,
            content={
                "status": "error",
                "msg": "Too many requests. Try again after some time."
            }
        )
        
    @app.exception_handler(httpx.HTTPStatusError)
    async def httpx_status_error_handler(request: Request, exc: httpx.HTTPStatusError):
        
        provider_error = exc.response.json()
        logger.warning(f"Error occured: {provider_error}")
        if provider_error.get("code") == 401:
            
            return JSONResponse(
                status_code= 503,
                content= {
                    "status": "error",
                    "msg": provider_error.get("message", "Unknown error"),
                })
            
        return JSONResponse(
            status_code= 503,
            content= {
                "status": "error",
                "msg": "Weather provider is unavailable.",
            },
        )
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled error {exc}", exc_info= True)
        return JSONResponse(
            status_code= 500,
            content= {
                "status":"error",
                "msg":"Something went wrong, try again later."
            }
        )



