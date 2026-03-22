import hashlib
import token

from app.repositories import UsuarioRepository, PerfilRepository, ResetPasswordTokenRepository
from app.schemas.usuario_schema import UsuarioFormData, UsuarioResetSenhaFormData
from app.schemas.response_schema import ResponseMessage
from app.dto.usuario_DTO import UsuarioPublicDTO, UsuarioModelDTO
from app.schemas.paginated_schema import PaginatedResponse
from datetime import datetime, timezone
from typing import List, Optional
from app.core.security import get_password_hash
from app.log_config.logging_config import get_logger
import secrets

logger = get_logger(__name__)
class UsuarioService:

    def __init__(self, session ):
        self.usuario_repository = UsuarioRepository(session=session)
        self.perfil_repository = PerfilRepository(session=session)
        self.reset_pass_repository = ResetPasswordTokenRepository(session=session)

    
    def create_usuario(self, data:UsuarioFormData) -> UsuarioPublicDTO | None:
        try: 
            usuario = self.usuario_repository.get_by_kwargs(uid=data.uid, email=data.email)
            if usuario:
                raise ValueError("UID or Email already exists") #TODO: Custom Exception
            if data.password is None:
                raise ValueError("Password is required") #TODO: Custom Exception
            password = data.password
            hashed_pass = get_password_hash(password)
            data.password = hashed_pass

            new_usuario = self.usuario_repository.create_usuario(data=data)

            if new_usuario:
                usuario_public_dto = UsuarioPublicDTO(
                    **new_usuario.model_dump(exclude={"hashed_pass", "perfil_id", "tokens", "id_usuario"})
                )
                return usuario_public_dto
        except Exception as e:
            print(f"[USUARIO SERVICE - ERROR] Failed to create usuario: {e}")
            return None

    def get_total_usuarios(self, **kwargs) -> int:
        try:
            total = self.usuario_repository.get_count_with_filters_ilike(**kwargs)
            return total
        except Exception as e:
            logger.error(f"Failed to count usuarios: {e}")
            return 0

    def get_all_usuarios(self, skip: int=0, limit: int=10, name_filter: Optional[str] = None, perfil_filter: Optional[str] = None) -> PaginatedResponse[UsuarioPublicDTO]:
        empty_reponse = PaginatedResponse(
                    items=[],
                    total_items=0,
                    total_pages=0,
                    page=(skip // limit) + 1,
                    skip=skip,
                    limit=limit
        )
        
        try:
            filters = {}
            if name_filter:
                filters['nome'] = name_filter
            if perfil_filter:
                perfil = self.perfil_repository.get_by_kwargs(valor=perfil_filter)
                if not perfil:
                    logger.warning(f"Perfil with name '{perfil_filter}' not found. Ignoring perfil filter.")
                else:
                    filters['perfil_id'] = perfil.id_perfil

            total_usuarios = self.get_total_usuarios(**filters)
            if total_usuarios == 0:
                return empty_reponse
            
            usuarios = self.usuario_repository.get_all_paginated_ilike(skip=skip, limit=limit, **filters)
            if not usuarios:
                return empty_reponse
            
            usuarios_public_dto = [
                UsuarioPublicDTO(
                **usuario.model_dump(exclude={"hashed_pass", "perfil_id", "tokens", "id_usuario"})
                )
                for usuario in usuarios
            ]
            return PaginatedResponse(
                items=usuarios_public_dto,
                total_items=total_usuarios,
                total_pages=(total_usuarios + limit - 1) // limit if limit > 0 else 1,
                page=(skip // limit) + 1,
                skip=skip,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Failed to retrieve usuarios: {e}")
            return empty_reponse

    def update_usuario(self, data: UsuarioFormData) -> ResponseMessage:
        try:
            usuario = self.usuario_repository.get_by_kwargs(uid=data.uid)
            if not usuario:
                raise ValueError("Usuario not found") #TODO: Custom Exception
            
            perfil = self.perfil_repository.get_by_kwargs(valor=data.perfil) if data.perfil else None
            if data.perfil and not perfil:
                raise ValueError("Perfil not found") #TODO: Custom Exception
            new_usuario_dto = UsuarioModelDTO(
                **usuario.model_dump(exclude={"perfil_id", "tokens", "nome", "email", "is_active", "perfil_id"}),
                nome=data.nome,
                email=data.email,
                is_active=data.ativo,
                perfil_id=perfil.id_perfil if perfil else usuario.perfil_id,

            )
            logger.warning(f"Fetched usuario for update: {new_usuario_dto}")
            if data.password and data.password != "":
                hashed_pass = get_password_hash(data.password)
                new_usuario_dto.hashed_pass = hashed_pass
            else:
                new_usuario_dto.hashed_pass = usuario.hashed_pass
            
            self.usuario_repository.update_usuario(new_usuario_dto)
            return ResponseMessage(success=True, message="Usuario updated successfully.")
        except Exception as e:
            logger.error(f"Failed to update usuario: {e}")
            return ResponseMessage(success=False, message="Failed to update usuario.")

    def delete_usuario(self, uid:str) -> ResponseMessage:
        try:
            usuario = self.usuario_repository.get_by_kwargs(uid=uid)
            if not usuario:
                raise ValueError("Usuario not found") #TODO: Custom Exception
            logger.warning(f"Fetched usuario for deletion: {usuario}")
            self.usuario_repository.delete(usuario)
            return ResponseMessage(success=True, message="Usuario deleted successfully.")
        except Exception as e:
            logger.error(f"Failed to delete usuario: {e}")
            return ResponseMessage(success=False, message="Failed to delete usuario.")

    def reset_password_usuario(self, data: UsuarioResetSenhaFormData) -> ResponseMessage:
        #Verify if the token is valid 
        hashed_token = hashlib.sha256(data.token.encode()).hexdigest()
        token = self.reset_pass_repository.get_by_kwargs(token=hashed_token)
        logger.warning(f"fetched token = {token} for provided reset token.")
        if token and not token.is_revoked:
            now_ref = datetime.now(token.exp.tzinfo) if token.exp.tzinfo else datetime.now()
            logger.warning(f"Token expiration time: {token.exp}, Current time ref: {now_ref}")
            if token.exp > now_ref:
                usuario = self.usuario_repository.get_by_kwargs(id_usuario=token.usuario_id)
                if not usuario:
                    logger.error(f"User associated with token not found: {token.usuario_id}")
                    return ResponseMessage(success=False, message="Invalid token.")
            
                hashed_pass = get_password_hash(data.new_password)
                new_usuario_dto = UsuarioModelDTO(
                    **usuario.model_dump(exclude={"hashed_pass"}),
                    hashed_pass=hashed_pass)
            
                self.usuario_repository.update_usuario(new_usuario_dto)
                #Revoke the token after use
                self.reset_pass_repository.revoke_token(id_token=token.id_token)

                return ResponseMessage(success=True, message="Password reset successful.")
            else:
                logger.warning(f"Token expired: {data.token}")
                return ResponseMessage(success=False, message="Token expired.")
        else:
            logger.warning(f"Invalid or expired token used for password reset: {data.token}")
            return ResponseMessage(success=False, message="Invalid or expired token.")