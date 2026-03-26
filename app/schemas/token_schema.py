from pydantic import BaseModel

from app.models.usuario_model import UsuarioModel


class TokenAuth(BaseModel):
    exp: int
    is_revoked: bool
    token: str
    usuario: UsuarioModel


class TokenResponse(BaseModel):
    """
    Schema for token who will be returned to the frontend.
    """

    token: str
    # refresh_token: str
    exp: int
    type: str = "bearer"


class TokenRefreshRequest(BaseModel):
    """
    Token sent by the frontend to refresh the access token.
    """

    refresh_token: str
