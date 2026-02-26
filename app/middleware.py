"""Middleware for request/response logging.

PG-004: Monitoring - Request logging middleware
"""
import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.logging_config import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests with timing and status."""
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        
        # Skip logging for static files and health checks in production
        path = request.url.path
        if path.startswith("/static/") or path.startswith("/uploads/"):
            if path == "/health":
                return await call_next(request)
            # Still log but at DEBUG level
            return await call_next(request)
        
        # Start timer
        start_time = time.time()
        
        # Log request start
        extra = {
            "request_id": request_id,
            "method": request.method,
            "endpoint": path,
            "query_params": str(request.query_params),
        }
        logger.debug(f"Request started", extra=extra)
        
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = round((time.time() - start_time) * 1000, 2)
            
            # Log successful response
            log_extra = {
                "request_id": request_id,
                "method": request.method,
                "endpoint": path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            }
            
            # Log at appropriate level based on status code
            if response.status_code >= 500:
                logger.error(f"Server error {response.status_code}", extra=log_extra)
            elif response.status_code >= 400:
                logger.warning(f"Client error {response.status_code}", extra=log_extra)
            else:
                logger.info(f"Request completed", extra=log_extra)
                
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calculate duration even for exceptions
            duration_ms = round((time.time() - start_time) * 1000, 2)
            
            log_extra = {
                "request_id": request_id,
                "method": request.method,
                "endpoint": path,
                "duration_ms": duration_ms,
            }
            logger.exception(f"Request failed: {str(e)}", extra=log_extra)
            raise


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to catch and log unhandled exceptions."""
    
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            request_id = getattr(request.state, 'request_id', 'unknown')
            logger.exception(
                f"Unhandled exception in {request.method} {request.url.path}",
                extra={"request_id": request_id}
            )
            raise
