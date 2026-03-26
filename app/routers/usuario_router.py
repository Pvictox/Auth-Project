from typing import Annotated
from fastapi import APIRouter, Depends, Form, HTTPException, Query, status
from sqlmodel import Session
from app.core.roles_checker import RolesChecker
from app.core.security import get_current_user
from app.database import get_session
from app.dto import TokenAuthenticatedDataDTO
from app.dto.usuario_dto import UsuarioPublicDTO
from app.log_config.logging_config import get_logger
from app.redis_cache import redis_invalidate
from app.schemas.paginated_schema import PaginatedResponse
from app.schemas.response_schema import ResponseMessage
from app.services.usuario_service import UsuarioService
from app.schemas.usuario_schema import (
    UsuarioFormData,
    UsuarioDeleteFormData,
    UsuarioResetSenhaFormData,
)

logger = get_logger(__name__)

router = APIRouter(
    prefix="/usuarios",
    tags=["usuarios"],
    responses={404: {"description": "Not found"}},
)


_admin_required = RolesChecker(allowed_roles=["admin"])
_usuario_required = RolesChecker(allowed_roles=["usuario"])

SessionDependency = Annotated[Session, Depends(get_session)]


@router.get(
    "/",
    tags=["usuarios"],
    status_code=status.HTTP_200_OK,
    response_model=PaginatedResponse[UsuarioPublicDTO],
)
# @redis_cache(ttl=180, key_prefix=f"usuarios:{{page}}:{{limit}}")
async def read_usuarios(
    session: SessionDependency,
    current_user=Depends(get_current_user),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=5, ge=1),
    name: str | None = Query(default=None, description="Optional name filter"),
    perfil: str | None = Query(
        default=None, description="Optional perfil filter"
    ),
) -> PaginatedResponse[UsuarioPublicDTO]:
    usuario_service = UsuarioService(session=session)
    usuarios = usuario_service.get_all_usuarios(
        skip=(page - 1) * limit,
        limit=limit,
        name_filter=name,
        perfil_filter=perfil,
    )
    return usuarios


@router.get("/total", tags=["usuarios"], status_code=status.HTTP_200_OK)
async def get_total_usuarios(
    session: SessionDependency,
    current_user=Annotated[
        TokenAuthenticatedDataDTO, Depends(get_current_user)
    ],
) -> dict:
    usuario_service = UsuarioService(session=session)
    total = usuario_service.get_total_usuarios()
    return {"success": True, "total": total}


@router.post(
    "/",
    tags=["usuarios"],
    status_code=status.HTTP_201_CREATED,
    response_model=ResponseMessage,
    dependencies=[Depends(_admin_required)],
)  # TODO: Ajustar retorno
@redis_invalidate("usuarios:*")  # Invalida cache de listagem de usuarios
async def create_usuario(
    data: Annotated[UsuarioFormData, Form()], session: SessionDependency
) -> ResponseMessage | None:
    usuario_service = UsuarioService(session=session)
    print("[USUARIO ROUTER - INFO] Creating new usuario...")
    new_usuario = usuario_service.create_usuario(data=data)
    if not new_usuario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create usuario.",
        )
    return ResponseMessage(
        success=True, message="Usuario created successfully."
    )


@router.put(
    "/update",
    tags=["usuarios"],
    status_code=status.HTTP_200_OK,
    response_model=ResponseMessage,
)
async def update_usuario(
    data: Annotated[UsuarioFormData, Form()],
    session: SessionDependency,
    current_user=Depends(get_current_user),
) -> ResponseMessage:
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )

    usuario_service = UsuarioService(session=session)
    return usuario_service.update_usuario(data=data)


@router.delete(
    "/delete",
    tags=["usuarios"],
    status_code=status.HTTP_200_OK,
    response_model=ResponseMessage,
)
async def delete_usuario(
    data: Annotated[UsuarioDeleteFormData, Form()],
    session: SessionDependency,
    current_user=Depends(get_current_user),
) -> ResponseMessage:
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )

    usuario_service = UsuarioService(session=session)
    return usuario_service.delete_usuario(uid=data.uid)


@router.post(
    "/reset-password",
    tags=["usuarios"],
    status_code=status.HTTP_200_OK,
    response_model=ResponseMessage,
)
async def reset_password(
    data: Annotated[UsuarioResetSenhaFormData, Form()],
    session: SessionDependency,
) -> ResponseMessage:
    usuario_service = UsuarioService(session=session)
    result = usuario_service.reset_password_usuario(data=data)
    return result
