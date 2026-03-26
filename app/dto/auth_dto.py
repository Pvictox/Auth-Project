from pydantic import BaseModel

from app.dto.usuario_dto import UsuarioTokenDTO


class TokenAuthenticatedDataDTO(BaseModel):
    """
    DTO for data extracted from a validated token.
    """

    user: UsuarioTokenDTO
