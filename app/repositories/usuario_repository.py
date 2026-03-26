from sqlmodel import Session, col, func, select
from unidecode import unidecode
from app.dto.usuario_dto import UsuarioModelDTO
from app.log_config.logging_config import get_logger
from app.models.usuario_model import UsuarioModel
from app.repositories import PerfilRepository
from app.repositories.base_repository import BaseRepository
from app.schemas.usuario_schema import UsuarioFormData

logger = get_logger(__name__)


class UsuarioRepository(BaseRepository[UsuarioModel, UsuarioModelDTO]):
    model = UsuarioModel
    dto = UsuarioModelDTO

    def __init__(self, session: Session):
        super().__init__(session)
        self.perfil_repository = PerfilRepository(session=session)

    def create_usuario(self, data: UsuarioFormData) -> UsuarioModelDTO | None:
        try:
            perfil_nome = data.perfil
            perfil = self.perfil_repository.get_by_kwargs(
                valor=unidecode(perfil_nome.lower())
            )
            if not perfil:
                logger.error(
                    "Perfil '%s' not found. Cannot create usuario.",
                    perfil_nome,
                )
                return None
            if (
                data.password is None
            ):  # This case will never trigger at creaton, but it's a safeguard for future updates where password might be optional
                logger.error("Password is required to create usuario.")
                return None
            new_usuario = UsuarioModel(
                nome=data.nome,
                perfil_id=perfil.id_perfil,
                uid=data.uid,
                email=data.email,
                hashed_pass=data.password,
                is_active=data.ativo,
            )
            self.session.add(new_usuario)
            self.session.commit()
            self.session.refresh(new_usuario)
            logger.warning(
                "New usuario created with id %d.", new_usuario.id_usuario
            )
            usuario_return = UsuarioModelDTO.model_validate(new_usuario)
            return usuario_return
        except Exception as e:
            self.session.rollback()
            logger.error("Failed to create new usuario: %s", e)
            return None

    def update_usuario(self, data: UsuarioModelDTO) -> UsuarioModelDTO | None:
        try:
            db_usuario = self.session.get(UsuarioModel, data.id_usuario)
            if not db_usuario:
                logger.warning(
                    "Usuario with id %d not found in database. Cannot update.",
                    data.id_usuario,
                )
                return None

            for field, value in data.model_dump(
                exclude={"id_usuario", "perfil", "tokens"}
            ).items():
                setattr(db_usuario, field, value)

            self.session.add(db_usuario)
            self.session.commit()
            self.session.refresh(db_usuario)
            return self.dto.model_validate(db_usuario)
        except Exception as e:
            self.session.rollback()
            logger.error(
                "Failed to update usuario with id %d: %s", data.id_usuario, e
            )
            raise

    def get_count_with_filters_ilike(self, **kwargs) -> int:
        nome_filter = kwargs.get("nome")
        perfil_id_filter = kwargs.get("perfil_id")

        statement = select(func.count()).select_from(self.model)
        if nome_filter:
            statement = statement.where(
                col(UsuarioModel.nome).ilike(f"%{nome_filter}%")
            )

        if perfil_id_filter:
            statement = statement.where(
                UsuarioModel.perfil_id == perfil_id_filter
            )

        count = self.session.exec(statement).one()
        return count

    def get_all_paginated_ilike(
        self, skip: int = 0, limit: int = 10, **kwargs
    ) -> list[UsuarioModelDTO]:
        nome_filter = kwargs.get("nome")
        perfil_id_filter = kwargs.get("perfil_id")

        statement = select(self.model)
        if nome_filter:
            statement = statement.where(
                col(UsuarioModel.nome).ilike(f"%{nome_filter}%")
            )

        if perfil_id_filter:
            statement = statement.where(
                UsuarioModel.perfil_id == perfil_id_filter
            )

        statement = statement.offset(skip).limit(limit)
        instances = self.session.exec(statement).all()

        return [self.dto.model_validate(instance) for instance in instances]
