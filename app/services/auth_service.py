import asyncio
from datetime import UTC, datetime, timedelta
import hashlib
import secrets

from dotenv import load_dotenv
from fastapi import Response
from fastapi.exceptions import HTTPException

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
)
from app.dto import (
    LoginRequestDTO,
    TokenModelCreateDTO,
    UsuarioPublicDTO,
    UsuarioTokenDTO,
)
from app.dto.reset_password_token_dto import (
    ResetPasswordTokenCreateDTO,
)
from app.log_config.logging_config import get_logger
from app.repositories import (
    ResetPasswordTokenRepository,
    TokenRepository,
    UsuarioRepository,
)
from app.schemas.login_schema import LogoutResponse, SucessfulLoginResponse
from app.services.mail_service import MailService

load_dotenv()

logger = get_logger(__name__)


class AuthService:
    def __init__(self, session):
        self.usuario_repository = UsuarioRepository(session=session)
        self.token_repository = TokenRepository(session=session)
        self.reset_password_token_repository = ResetPasswordTokenRepository(
            session=session
        )
        self.mail_service = MailService()

    def handle_login(
        self, data: LoginRequestDTO, response: Response
    ) -> SucessfulLoginResponse | None:
        try:
            usuario = self.usuario_repository.get_by_kwargs(uid=data.uid)
            if not usuario or not verify_password(
                data.password, usuario.hashed_pass
            ):
                return None
            if not usuario.is_active:
                raise ValueError("User is inactive")  # TODO: Custom Exception

            usuario_token = UsuarioTokenDTO(
                **usuario.model_dump(
                    exclude={
                        "id_usuario",
                        "hashed_pass",
                        "perfil_id",
                        "tokens",
                    }
                )
            )

            access_token = create_access_token(usuario=usuario_token)
            refresh_token, expiration = create_refresh_token()

            refresh_token_create_dto = TokenModelCreateDTO(
                token=refresh_token,
                exp=datetime.fromtimestamp(expiration),
                usuario_id=usuario.id_usuario,
            )

            self.token_repository.save_refresh_token(
                new_refresh_token=refresh_token_create_dto
            )

            is_production = settings.ENVIRONMENT == "production"

            response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,
                secure=is_production,
                samesite="lax",
                max_age=int(settings.ACESS_TOKEN_EXPIRE_MINUTES) * 60,  # type:ignore
            )

            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=is_production,
                samesite="lax",
                max_age=int(settings.REFRESH_TOKEN_EXPIRE_MINUTES) * 60,  # type:ignore
            )

            return SucessfulLoginResponse(
                user=UsuarioPublicDTO(**usuario_token.model_dump()),
            )

        except ValueError as ve:  # Case of inactive user
            logger.warning("Login attempt failed: %s", ve)
            raise HTTPException(status_code=403, detail=str(ve)) from ve

        except Exception as e:
            logger.error("Failed to handle login: %s", e)
            return None

    def refresh_acess_token(
        self, refresh_token: str, response: Response
    ) -> SucessfulLoginResponse | None:
        try:
            stored_refresh_token = self.token_repository.get_by_kwargs(
                token=refresh_token
            )
            if not stored_refresh_token:
                raise HTTPException(
                    status_code=401, detail="Invalid refresh token"
                )

            if stored_refresh_token.is_revoked:
                raise HTTPException(
                    status_code=401, detail="Refresh token has been revoked"
                )

            if (
                stored_refresh_token.exp.timestamp()
                < datetime.now().timestamp()
            ):
                raise HTTPException(
                    status_code=401, detail="Refresh token has expired"
                )

            usuario = self.usuario_repository.get_by_kwargs(
                id_usuario=stored_refresh_token.usuario_id
            )
            if not usuario:
                raise HTTPException(status_code=404, detail="User not found")

            self.token_repository.delete(stored_refresh_token)

            usuario_public = UsuarioPublicDTO(
                uid=usuario.uid,
                perfil=usuario.perfil.valor,
                email=usuario.email,
                is_active=usuario.is_active,
                nome=usuario.nome,
            )

            access_token = create_access_token(usuario=usuario_public)
            new_refresh_token, expiration = create_refresh_token()

            resfresh_token_create_dto = TokenModelCreateDTO(
                token=new_refresh_token,
                exp=datetime.fromtimestamp(expiration),
                usuario_id=usuario.id_usuario,
            )

            self.token_repository.save_refresh_token(
                new_refresh_token=resfresh_token_create_dto
            )

            is_production = settings.ENVIRONMENT == "production"
            response.delete_cookie("access_token")
            response.delete_cookie("refresh_token")
            response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,
                secure=is_production,
                samesite="lax",
                max_age=int(settings.ACESS_TOKEN_EXPIRE_MINUTES) * 60,  # type:ignore
            )

            response.set_cookie(
                key="refresh_token",
                value=new_refresh_token,
                httponly=True,
                secure=is_production,
                samesite="lax",
                max_age=int(settings.REFRESH_TOKEN_EXPIRE_MINUTES) * 60,  # type:ignore
            )

            return SucessfulLoginResponse(
                user=usuario_public,
            )

        except HTTPException as http_exc:
            raise http_exc

    async def forgot_password(self, email: str) -> dict:
        token = secrets.token_urlsafe(32)
        hashed_token = hashlib.sha256(token.encode()).hexdigest()
        expiration = datetime.now(UTC) + timedelta(minutes=5)
        usuario = self.usuario_repository.get_by_kwargs(email=email)
        if usuario:
            reset_token_dto = ResetPasswordTokenCreateDTO(
                token=hashed_token,
                exp=expiration,
                usuario_id=usuario.id_usuario,
            )
            self.reset_password_token_repository.save_reset_password_token(
                new_token=reset_token_dto
            )
            await self.mail_service.send_password_reset_email(
                email=email, token=token
            )
        else:
            # simulate the same response time to prevent user enumeration
            await asyncio.sleep(4)
            logger.warning("No user found with email: %s", email)

        return {
            "message": "If an account with that email exists, a reset token has been sent."
        }

    def logout(
        self, response: Response, refresh_token: str | None
    ) -> LogoutResponse:
        try:
            if refresh_token:
                stored_refresh_token = self.token_repository.get_by_kwargs(
                    token=refresh_token
                )
                if stored_refresh_token:
                    self.token_repository.delete(stored_refresh_token)

            response.delete_cookie("access_token")
            response.delete_cookie("refresh_token")

            return LogoutResponse(
                success=True, message="Logged out successfully"
            )
        except Exception as e:
            logger.error("Failed to handle logout: %s", e)
            return LogoutResponse(success=False, message="Failed to log out")
