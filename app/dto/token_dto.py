from datetime import datetime
from pydantic import BaseModel
from sqlmodel import SQLModel


class TokenModelDTO(SQLModel):
    id_token: int
    token: str
    exp: datetime
    created_at: datetime
    is_revoked: bool
    usuario_id: int

    class Config:
        from_attributes = True


class TokenModelCreateDTO(BaseModel):
    """
    DTO for token creation.
    """

    token: str
    exp: datetime
    is_revoked: bool = False
    created_at: datetime = datetime.now()
    usuario_id: int


class RefreshTokenCreate(BaseModel):
    """
    DTO for refresh token creation.
    """

    refresh_token: str
    exp: int
    is_revoked: bool = False
    created_at: datetime = datetime.now()
    usuario_id: int
