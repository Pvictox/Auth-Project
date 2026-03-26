from sqlmodel import Session

from app.dto.reset_password_token_dto import (
    ResetPasswordTokenCreateDTO,
    ResetPasswordTokenDTO,
)
from app.log_config.logging_config import get_logger
from app.models import ResetPasswordTokenModel
from app.repositories.base_repository import BaseRepository

logger = get_logger(__name__)


class ResetPasswordTokenRepository(
    BaseRepository[ResetPasswordTokenModel, ResetPasswordTokenDTO]
):
    model = ResetPasswordTokenModel
    dto = ResetPasswordTokenDTO

    def __init__(self, session: Session):
        super().__init__(session)

    def save_reset_password_token(
        self, new_token: ResetPasswordTokenCreateDTO
    ) -> ResetPasswordTokenDTO:
        try:
            reset_token_model = ResetPasswordTokenModel(
                **new_token.model_dump()
            )
            self.session.add(reset_token_model)
            self.session.commit()
            self.session.refresh(reset_token_model)
            return ResetPasswordTokenDTO(**reset_token_model.model_dump())
        except Exception as e:
            self.session.rollback()
            logger.error("Failed to create new reset password token: %s", e)
            raise

    def revoke_token(self, id_token: int) -> bool:
        try:
            token = self.session.get(ResetPasswordTokenModel, id_token)
            if not token:
                logger.warning(
                    "Token with id %d not found for revocation.", id_token
                )
                return False
            token.is_revoked = True
            self.session.add(token)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            logger.error("Failed to revoke token with id %d: %s", id_token, e)
            return False
