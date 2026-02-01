# # app/utils/auth.py
# from fastapi import Depends, status
# from fastapi.security import APIKeyHeader
# from app.utils.exceptions import InvalidAPIKeyException
# from config import settings
# import logging

# logger = logging.getLogger(__name__)

# api_key_header = APIKeyHeader(name="X-API-Key")

# async def verify_api_key(api_key: str = Depends(api_key_header)) -> str:
#     """
#     Verify API key from request header
#     SECURITY: Never log the actual API key value
#     """
#     # Check if API key is configured
#     if not settings.SUMSUB_API_KEY or settings.SUMSUB_API_KEY == "your-api-key-here":
#         logger.error("API key not configured properly in environment")
#         raise InvalidAPIKeyException()
    
#     # Validate key length (basic check)
#     if not api_key or len(api_key) < 10:
#         logger.warning(f"Invalid API key format from request")
#         raise InvalidAPIKeyException()
    
#     # Compare securely
#     if api_key != settings.SUMSUB_API_KEY:
#         logger.warning(f"API key mismatch - unauthorized access attempt")
#         raise InvalidAPIKeyException()
    
#     return api_key