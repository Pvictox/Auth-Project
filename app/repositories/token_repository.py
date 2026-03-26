from sqlmodel import Session

from app.dto.token_dto import TokenModelCreateDTO, TokenModelDTO
from app.log_config.logging_config import get_logger
from app.models.token_model import TokenModel
from app.repositories.base_repository import BaseRepository
from app.schemas.token_schema import TokenResponse

logger = get_logger(__name__)


class TokenRepository(BaseRepository[TokenModel, TokenModelDTO]):
    model = TokenModel
    dto = TokenModelDTO

    def __init__(self, session: Session):
        super().__init__(session)

    def save_refresh_token(
        self, new_refresh_token: TokenModelCreateDTO
    ) -> TokenResponse:
        try:
            token_model = TokenModel(**new_refresh_token.model_dump())
            self.session.add(token_model)
            self.session.commit()
            self.session.refresh(token_model)
            return TokenResponse(
                token=token_model.token, exp=int(token_model.exp.timestamp())
            )
        except Exception as e:
            self.session.rollback()
            print(
                f"[TOKEN REPOSITORY - ERROR] Failed to create new token: {e}"
            )
            raise
