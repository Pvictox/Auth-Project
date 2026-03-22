from fastapi import APIRouter, Depends, status, HTTPException, Form, Query
from app.schemas.perfil_schema import PerfilPublic
from app.database import Database, get_session
from typing import Annotated, List
from sqlmodel import Session
from app.services.perfil_service import PerfilService
from app.schemas.paginated_schema import PaginatedResponse
from app.redis_cache import redis_cache, redis_invalidate
from app.core.security import get_current_user

router = APIRouter(
    prefix="/perfis",
    tags=["perfis"],
    responses={404: {"description": "Not found"}},)

SessionDependency = Annotated[ Session, Depends(get_session) ]


@router.get("/", status_code=status.HTTP_200_OK, response_model=PaginatedResponse[PerfilPublic])
#@redis_cache(ttl=180, key_prefix=f"perfis:{{page}}:{{limit}}")
async def read_perfis(session: SessionDependency, current_user = Depends(get_current_user),
                      page: int = Query(default=1, ge=1),
                        limit: int = Query(default=10, ge=1)) -> PaginatedResponse[PerfilPublic]:
    perfil_service = PerfilService(session=session)
    return perfil_service.get_all_perfis(skip=(page-1)*limit, limit=limit)