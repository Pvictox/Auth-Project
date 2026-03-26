from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.core.security import get_current_user
from app.database import Database, get_session
from app.log_config.logging_config import get_logger
from app.schemas.health_schema import HealthStatus

logger = get_logger(__name__)

router = APIRouter(
    prefix="/system",
    tags=["system"],
    responses={404: {"description": "Not found"}},
)

SessionDependency = Annotated[Session, Depends(get_session)]


@router.get("/health", tags=["system"], status_code=status.HTTP_200_OK)
async def get_system_health(
    session: SessionDependency, current_user=Depends(get_current_user)
) -> list:
    database = Database()
    response = []
    db_status = database.check_connection()
    if db_status:
        response.append(
            HealthStatus(
                id=1, title="Banco de Dados", status="online"
            ).model_dump()
        )
    else:
        response.append(
            HealthStatus(
                id=1, title="Banco de Dados", status="error"
            ).model_dump()
        )

    response.append(
        HealthStatus(id=2, title="API", status="online").model_dump()
    )

    return response
