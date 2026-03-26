from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer

from app.log_config.logging_config import get_logger

logger = get_logger(__name__)


class CookieBearer(HTTPBearer):
    async def __call__(self, request: Request) -> str:
        # logger.debug(f"Acess_token extracted from cookies: {request.cookies.get('access_token')}")
        token = request.cookies.get("access_token")

        if not token:
            # Fallback for compatibility
            authorization: str | None = request.headers.get("Authorization")
            if authorization:
                scheme, credentials = authorization.split()
                if scheme.lower() == "bearer":
                    token = credentials

        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You're not authenticated. Please provide an access token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return token
