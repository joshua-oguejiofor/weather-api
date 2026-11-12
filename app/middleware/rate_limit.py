from app.core.config import settings
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler, Limiter
from fastapi import FastAPI





limiter= Limiter(
    key_func= get_remote_address,
    storage_uri= settings.REDIS_URL,
    default_limits= ["100/minute"]
)




def setup_rate_limiter(app: FastAPI):
    
    app.state.limiter= limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_exception_handler(
        RateLimitExceeded,
        _rate_limit_exceeded_handler
    )
    