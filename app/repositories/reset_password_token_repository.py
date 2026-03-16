
from app.models import ResetPasswordTokenModel
from app.dto.reset_password_token_DTO import ResetPasswordTokenDTO, ResetPasswordTokenCreateDTO
from sqlmodel import Session
from app.log_config.logging_config import get_logger
from app.repositories.base_repository import BaseRepository

logger = get_logger(__name__)

class ResetPasswordTokenRepository(BaseRepository[ResetPasswordTokenModel, ResetPasswordTokenDTO]):
    model = ResetPasswordTokenModel
    dto = ResetPasswordTokenDTO

    def __init__(self, session: Session):
        super().__init__(session)
   
    def save_reset_password_token(self, new_token: ResetPasswordTokenCreateDTO) -> ResetPasswordTokenDTO:
        try:
            reset_token_model = ResetPasswordTokenModel(**new_token.model_dump())
            self.session.add(reset_token_model)
            self.session.commit()
            self.session.refresh(reset_token_model)
            return ResetPasswordTokenDTO(**reset_token_model.model_dump())
        except Exception as e:
            self.session.rollback()
            logger.error(f"[RESET PASSWORD TOKEN REPOSITORY - ERROR] Failed to create new reset password token: {e}")
            raise