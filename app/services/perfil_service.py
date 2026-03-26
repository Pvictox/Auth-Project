from app.dto.perfil_dto import PerfilModelDTO
from app.log_config.logging_config import get_logger
from app.repositories.perfil_repository import PerfilRepository
from app.schemas.paginated_schema import PaginatedResponse
from app.schemas.perfil_schema import PerfilPublic

logger = get_logger(__name__)


class PerfilService:
    def __init__(self, session) -> None:
        self.perfil_repository = PerfilRepository(session=session)

    def get_all_perfis(
        self, skip: int = 0, limit: int = 10
    ) -> PaginatedResponse[PerfilPublic]:
        empty_reponse = PaginatedResponse(
            items=[],
            total_items=0,
            total_pages=0,
            page=(skip // limit) + 1,
            skip=skip,
            limit=limit,
        )
        total_perfis = self.perfil_repository.get_count()
        if total_perfis == 0:
            logger.warning("No perfis found in the database.")
            return empty_reponse

        perfis: list[PerfilModelDTO] = (
            self.perfil_repository.get_all_paginated(skip=skip, limit=limit)
        )

        entities = [PerfilPublic(valor=perfil.valor) for perfil in perfis]

        response = PaginatedResponse(
            items=entities,
            total_items=total_perfis,
            total_pages=(total_perfis + limit - 1) // limit
            if limit > 0
            else 1,
            page=(skip // limit) + 1,
            skip=skip,
            limit=limit,
        )

        return response
