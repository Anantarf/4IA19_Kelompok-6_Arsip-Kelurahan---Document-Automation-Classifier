"""
Security middleware helpers for rate limiting and headers
"""
from fastapi import FastAPI, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

# Initialize limiter
limiter = Limiter(key_func=get_remote_address)

def setup_rate_limiting(app: FastAPI):
    """Setup rate limiting middleware"""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, lambda request, exc: JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please try again later."},
    ))

# Rate limit decorators for common endpoints
RATE_LIMITS = {
    "health": "100/minute",
    "login": "5/minute",           # 5 attempts per minute
    "register": "3/minute",        # 3 attempts per minute
    "upload": "20/hour",           # 20 uploads per hour
    "search": "100/minute",        # 100 searches per minute
}
