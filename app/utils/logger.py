import logging
import sys
import time
import uuid
from functools import wraps
from starlette.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-8s  %(pathname)s:%(lineno)d %(funcName)s   %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)

# Get our app logger
logger = logging.getLogger(__name__)

class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Get request ID from headers
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = request.headers.get("X-Correlation-ID")
        if not request_id:
            request_id = request.headers.get("X-Trace-ID")
        if not request_id:
            request_id = str(uuid.uuid4())[:8]
        
        # Process the request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        return response

# class TimeFilter(logging.Filter):
#     """Custom logging filter to add execution time to log records."""
#     def filter(self, record):
#         """Calculate execution time using relativeCreated and current time."""
#         # Get the current time in milliseconds
#         current_time = time.perf_counter() * 1000  # Convert to milliseconds
        
#         # Calculate elapsed time
#         elapsed_time = (current_time - record.relativeCreated) / 1000.0  # Convert to seconds
#         record.execution_time = f"{elapsed_time:.2f}s"  # Set execution time
#         return True

# # Create an instance of the TimeFilter
# time_filter = TimeFilter()
# logger.addFilter(time_filter)

def log_execution_time(func):
    """Decorator to log function execution time using a logging filter."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        logger.info(f"Starting {func.__name__}")
        
        try:
            result = await func(*args, **kwargs)
            logger.info(f"Completed {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"Failed {func.__name__}: {str(e)}")
            return None
    return wrapper 