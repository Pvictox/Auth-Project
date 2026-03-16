from app.repositories import UsuarioRepository, TokenRepository, ResetPasswordTokenRepository
from fastapi.exceptions import HTTPException
from fastapi import Response
from app.dto import (LoginRequestDTO, 
                     UsuarioTokenDTO, TokenModelCreateDTO,
                     UsuarioPublicDTO)
from app.dto.reset_password_token_DTO import ResetPasswordTokenDTO, ResetPasswordTokenCreateDTO
from datetime import datetime
from typing import Optional
from app.schemas.login_schema import SucessfulLoginResponse, LogoutResponse
from app.core.config import settings
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
)
from app.services.mail_service import MailService
import secrets, hashlib
from dotenv import load_dotenv
from app.log_config.logging_config import get_logger


load_dotenv() 

logger = get_logger(__name__)
class AuthService:

    def __init__(self, session ):
        self.usuario_repository = UsuarioRepository(session=session)
        self.token_repository = TokenRepository(session=session)
        self.reset_password_token_repository = ResetPasswordTokenRepository(session=session)
        self.mail_service = MailService()
    
    def handle_login(self, data:LoginRequestDTO, response: Response) -> SucessfulLoginResponse | None:
        try: 
            usuario = self.usuario_repository.get_by_kwargs(uid=data.uid)
            if not usuario or not verify_password(data.password, usuario.hashed_pass):
                return None
            if not usuario.is_active:
                raise ValueError("User is inactive") #TODO: Custom Exception
            
            usuario_token = UsuarioTokenDTO(
                **usuario.model_dump(exclude={"id_usuario", "hashed_pass", "perfil_id", "tokens"})
            )

            access_token = create_access_token(usuario=usuario_token)
            refresh_token, expiration = create_refresh_token()

            refresh_token_create_dto = TokenModelCreateDTO(
                token= refresh_token,
                exp= datetime.fromtimestamp(expiration),
                usuario_id= usuario.id_usuario
            )

            refresh = self.token_repository.save_refresh_token(new_refresh_token=refresh_token_create_dto)

            is_production = settings.ENVIRONMENT == "production"

            #logger.debug(f"Setting access_token cookie with value: {access_token}")
            response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,
                secure=is_production,
                samesite='lax',
                max_age= int(settings.ACESS_TOKEN_EXPIRE_MINUTES) * 60 #type:ignore
            )

            #logger.warning(f"Setting refresh_token cookie with value: {refresh}")
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=is_production,
                samesite='lax',
                max_age= int(settings.REFRESH_TOKEN_EXPIRE_MINUTES) * 60 #type:ignore
            )

            return SucessfulLoginResponse(
                user= UsuarioPublicDTO(**usuario_token.model_dump()),
            )

        except Exception as e:
            logger.error(f"[AUTH SERVICE - ERROR] Failed to handle login: {e}")
            return None

    def refresh_acess_token(self, refresh_token: str, response: Response) -> SucessfulLoginResponse | None:
        try:
            stored_refresh_token = self.token_repository.get_by_kwargs(token = refresh_token)
            if not stored_refresh_token:
                raise HTTPException(status_code=401, detail="Invalid refresh token")
            
            if stored_refresh_token.is_revoked:
                raise HTTPException(status_code=401, detail="Refresh token has been revoked")

            if stored_refresh_token.exp.timestamp() < datetime.now().timestamp():
                raise HTTPException(status_code=401, detail="Refresh token has expired")

            usuario = self.usuario_repository.get_by_kwargs(id_usuario=stored_refresh_token.usuario_id)
            if not usuario:
                raise HTTPException(status_code=404, detail="User not found")
            
            self.token_repository.delete(stored_refresh_token)

            
            usuario_public = UsuarioPublicDTO(
                uid=usuario.uid,
                perfil=usuario.perfil.valor,
                email=usuario.email,
                is_active=usuario.is_active,
                nome = usuario.nome
            )
            
            access_token = create_access_token(usuario=usuario_public)
            new_refresh_token, expiration = create_refresh_token()

            resfresh_token_create_dto = TokenModelCreateDTO(
                token= new_refresh_token,
                exp= datetime.fromtimestamp(expiration),
                usuario_id= usuario.id_usuario)

            refresh = self.token_repository.save_refresh_token(new_refresh_token=resfresh_token_create_dto)

            

            is_production = settings.ENVIRONMENT == "production"
            response.delete_cookie("access_token")
            response.delete_cookie("refresh_token")
            logger.warning(f"Setting new access token cookie with value: {access_token}")
            response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,
                secure=is_production,
                samesite='lax',
                max_age= int(settings.ACESS_TOKEN_EXPIRE_MINUTES) * 60 #type:ignore
            )

            logger.warning(f"Setting new refresh token cookie with value: {new_refresh_token}")
            response.set_cookie(
                key="refresh_token",
                value=new_refresh_token,
                httponly=True,
                secure=is_production,
                samesite='lax',
                max_age= int(settings.REFRESH_TOKEN_EXPIRE_MINUTES) * 60 #type:ignore
            )

            return SucessfulLoginResponse(
                user=usuario_public,
            )
            
        except HTTPException as http_exc:
            raise http_exc

    async def forgot_password(self, email: str)-> dict:
        token = secrets.token_urlsafe(32)
        hashed_token = hashlib.sha256(token.encode()).hexdigest()
        expiration = datetime.now().timestamp() + 300 # 5 minutes
        usuario = self.usuario_repository.get_by_kwargs(email=email)
        if usuario:
            logger.warning(f"Creating reset password token for user with email: {email}")
            reset_token_dto = ResetPasswordTokenCreateDTO(
                token=hashed_token,
                exp=datetime.fromtimestamp(expiration),
                usuario_id=usuario.id_usuario,
            )
            self.reset_password_token_repository.save_reset_password_token(new_token=reset_token_dto)
            await self.mail_service.send_password_reset_email(email=email, token=token)
        else:
            logger.warning(f"No user found with email: {email}")
        
        return {"message": "If an account with that email exists, a reset token has been sent."}


    def logout(self, response: Response,  refresh_token: Optional[str])-> LogoutResponse:
        try:
            if refresh_token:
                stored_refresh_token = self.token_repository.get_by_kwargs(token = refresh_token)
                if stored_refresh_token:
                    self.token_repository.delete(stored_refresh_token)
            
            response.delete_cookie("access_token")
            response.delete_cookie("refresh_token")

            return LogoutResponse(
                success=True,
                message="Logged out successfully"
            )
        except Exception as e:
            logger.error(f"[AUTH SERVICE - ERROR] Failed to handle logout: {e}")
            return LogoutResponse(
                success=False,
                message="Failed to log out"
            )