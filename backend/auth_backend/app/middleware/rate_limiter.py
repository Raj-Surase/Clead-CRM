"""
Rate limiting middleware for authentication endpoints
"""
import time
from typing import Dict, Tuple
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware to prevent brute force attacks
    """
    
    def __init__(self, app, calls: int = 5, period: int = 60):
        super().__init__(app)
        self.calls = calls  # Number of calls allowed
        self.period = period  # Time period in seconds
        self.clients: Dict[str, list] = {}  # Store client request timestamps
        
        # Endpoints to apply rate limiting
        self.rate_limited_endpoints = {
            "/auth/login": {"calls": 5, "period": 300},  # 5 attempts per 5 minutes
            "/auth/register": {"calls": 3, "period": 300},  # 3 attempts per 5 minutes
            "/auth/forgot-password": {"calls": 3, "period": 600},  # 3 attempts per 10 minutes
            "/auth/reset-password": {"calls": 3, "period": 300},  # 3 attempts per 5 minutes
            "/auth/verify-email": {"calls": 5, "period": 300},  # 5 attempts per 5 minutes
        }

    def get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers first (for reverse proxy setups)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"

    def is_rate_limited(self, client_ip: str, endpoint: str) -> Tuple[bool, int]:
        """
        Check if client is rate limited for specific endpoint
        Returns (is_limited, retry_after_seconds)
        """
        if endpoint not in self.rate_limited_endpoints:
            return False, 0
        
        config = self.rate_limited_endpoints[endpoint]
        calls_limit = config["calls"]
        period = config["period"]
        
        current_time = time.time()
        client_key = f"{client_ip}:{endpoint}"
        
        # Initialize client record if not exists
        if client_key not in self.clients:
            self.clients[client_key] = []
        
        # Remove old timestamps outside the time window
        self.clients[client_key] = [
            timestamp for timestamp in self.clients[client_key]
            if current_time - timestamp < period
        ]
        
        # Check if limit exceeded
        if len(self.clients[client_key]) >= calls_limit:
            # Calculate retry after time
            oldest_timestamp = min(self.clients[client_key])
            retry_after = int(period - (current_time - oldest_timestamp)) + 1
            return True, retry_after
        
        # Add current timestamp
        self.clients[client_key].append(current_time)
        return False, 0

    def cleanup_old_entries(self):
        """Clean up old entries to prevent memory leaks"""
        current_time = time.time()
        max_period = max(config["period"] for config in self.rate_limited_endpoints.values())
        
        # Remove entries older than the maximum period
        for client_key in list(self.clients.keys()):
            self.clients[client_key] = [
                timestamp for timestamp in self.clients[client_key]
                if current_time - timestamp < max_period
            ]
            
            # Remove empty entries
            if not self.clients[client_key]:
                del self.clients[client_key]

    async def dispatch(self, request: Request, call_next):
        """Process the request and apply rate limiting"""
        # Only apply rate limiting to POST requests on auth endpoints
        if request.method == "POST" and request.url.path.startswith("/auth/"):
            client_ip = self.get_client_ip(request)
            endpoint = request.url.path
            
            # Check rate limit
            is_limited, retry_after = self.is_rate_limited(client_ip, endpoint)
            
            if is_limited:
                logger.warning(
                    f"Rate limit exceeded for {client_ip} on {endpoint}. "
                    f"Retry after {retry_after} seconds."
                )
                
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": "Too many requests. Please try again later.",
                        "retry_after": retry_after
                    },
                    headers={"Retry-After": str(retry_after)}
                )
            
            # Periodically cleanup old entries (every 100 requests)
            if len(self.clients) % 100 == 0:
                self.cleanup_old_entries()
        
        # Process the request
        response = await call_next(request)
        return response

