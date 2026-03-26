from datetime import UTC, datetime, timedelta
import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import Session

from app.core.config import settings
from app.core.cookie import CookieBearer
from app.database import get_session
from app.dto import TokenAuthenticatedDataDTO, UsuarioTokenDTO
from app.log_config.logging_config import get_logger

logger = get_logger(__name__)

pwd_context = CryptContext(
    schemes=[settings.CRYPT_CONTEXT_SCHEMES], deprecated="auto"
)
SessionDependency = Annotated[Session, Depends(get_session)]
cookie_scheme = CookieBearer()


async def get_current_user(
    token: str = Depends(cookie_scheme),
) -> TokenAuthenticatedDataDTO:
    # TODO: Create custom exceptions
    base_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # logger.warning(f"Received token for validation: {token}")
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user = payload.get("user")
        if user is None:
            raise base_exception
        token_data = TokenAuthenticatedDataDTO(
            user=UsuarioTokenDTO.model_validate_json(user)
        )
        return token_data
    except JWTError as e:
        logger.error("JWT decoding error: %s", str(e))
        raise base_exception from e
    except Exception as e:
        logger.error("Unexpected error during token validation: %s", str(e))
        raise base_exception from e


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(usuario: UsuarioTokenDTO) -> str:
    expire: datetime = datetime.now(UTC) + timedelta(
        minutes=settings.ACESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode = {
        "exp": int(expire.timestamp()),
        "int": int(datetime.now(UTC).timestamp()),
        "alg": settings.ALGORITHM,
        "user": usuario.model_dump_json(),
    }

    encoded_jwt: str = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token() -> tuple[str, int]:
    new_expire: datetime = datetime.now(UTC) + timedelta(
        minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
    )
    token = secrets.token_urlsafe(32)
    return token, int(new_expire.timestamp())
