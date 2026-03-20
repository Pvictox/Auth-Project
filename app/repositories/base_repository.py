from typing import Generic, Optional, TypeVar, Type, List
from sqlmodel import SQLModel, Session, select, func
from pydantic import BaseModel
from app.log_config.logging_config import get_logger
from sqlalchemy import inspect as sa_inspect

logger = get_logger(__name__)

ModelType = TypeVar("ModelType", bound=SQLModel)
DTOType = TypeVar("DTOType", bound=BaseModel)

class BaseRepository(Generic[ModelType, DTOType]):
    model: Type[ModelType]
    dto: Type[DTOType]

    
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_kwargs(self, **kwargs) -> DTOType | None:
        statement = select(self.model).filter_by(**kwargs)
        instance = self.session.exec(statement).first()
        if not instance:
            logger.warning(f"No {self.model.__name__} found with {kwargs}.")
            return None

        return self.dto.model_validate(instance)
    
    def get_all_by_kwargs(self, **kwargs) -> List[DTOType] | None:
        statement = select(self.model).filter_by(**kwargs)
        instances = self.session.exec(statement).all()
        if not instances:
            logger.warning(f"No {self.model.__name__} found with {kwargs}.")
            return None

        return [self.dto.model_validate(instance) for instance in instances]
    
    def get_all_not_paginated(self) -> List[DTOType] | None:
        statement = select(self.model)
        instances = self.session.exec(statement).all()
        if not instances:
            logger.warning(f"No {self.model.__name__} found in the database.")
            return None

        return [self.dto.model_validate(instance) for instance in instances]

    #Use only if you need a pagination with/without filters that are not ilike. For ilike filters, create a custom method in the repository (like get_all_paginated_ilike) and use it in the service.
    #Check 'UsuarioRepository.get_all_paginated_ilike' for an example of how to create a custom pagination method with ilike filters.
    def get_all_paginated(self, skip: int = 0, limit: int = 10, **kwargs) -> List[DTOType]:
        statement = select(self.model).filter_by(**kwargs).offset(skip).limit(limit)
        instances = self.session.exec(statement).all()
        return [self.dto.model_validate(instance) for instance in instances]
    
    
    #The same ideia applies to this function. Need a filter with ilike? Create a custom method in the repository and use it in the service.
    #Check 'UsuarioRepository.get_count_with_filters_ilike' for an example.
    def get_count(self, **kwargs) -> int:
        statement = select(func.count()).select_from(self.model).filter_by(**kwargs)
        count = self.session.exec(statement).one()
        return count

    #TODO: Change this function to ignore relationships fields.
    def update(self, instance_DTO: DTOType) -> DTOType | None:
        try:
            pk_name, pk_value = self._get_pk_value(instance_DTO)
            db_instance = self.session.get(self.model, pk_value)
            if not db_instance:
                logger.warning(f"{self.model.__name__} with {pk_name}={pk_value} not found in database. Cannot update.")
                return None

            for field, value in instance_DTO.model_dump().items():
                setattr(db_instance, field, value)

            self.session.add(db_instance)
            self.session.commit()
            self.session.refresh(db_instance)
            return self.dto.model_validate(db_instance)
        except Exception as e:
            self.session.rollback()
            logger.error(f"[{self.model.__name__.upper()} REPOSITORY - ERROR] Failed to update {self.model.__name__}: {e}")
            raise
    
    def create(self, instance_DTO: DTOType) -> DTOType | None:
        try:
            instance = self.model(**instance_DTO.model_dump())
            self.session.add(instance)
            self.session.commit()
            self.session.refresh(instance)
            return self.dto.model_validate(instance)
        except Exception as e:
            self.session.rollback()
            logger.error(f"[{self.model.__name__.upper()} REPOSITORY - ERROR] Failed to create {self.model.__name__}: {e}")
            raise
    

    def delete(self, instance_DTO: DTOType) -> None:
        try:
            pk_name, pk_value = self._get_pk_value(instance_DTO)
            db_instance = self.session.get(self.model, pk_value)
            if not db_instance:
                logger.warning(f"{self.model.__name__} with {pk_name}={pk_value} not found in database. Cannot delete.")
                return
            self.session.delete(db_instance)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            logger.error(f"[{self.model.__name__.upper()} REPOSITORY - ERROR] Failed to delete {self.model.__name__}: {e}")
            raise

    def _get_pk_value(self, dto: DTOType):
        mapper = sa_inspect(self.model)
        pk_columns = [col.key for col in mapper.mapper.primary_key]

        if len(pk_columns) > 1:
            raise NotImplementedError("Composite primary keys are not supported.")

        pk_name: str = pk_columns[0] #type: ignore
        pk_value = getattr(dto, pk_name, None)

        if pk_value is None:
            raise ValueError(f"DTO has no attribute '{pk_name}' or its value is None.")

        return pk_name, pk_value