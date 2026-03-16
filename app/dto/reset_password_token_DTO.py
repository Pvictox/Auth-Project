from sqlmodel import SQLModel

from datetime import datetime



class ResetPasswordTokenDTO(SQLModel):
    id_token: int
    token: str
    exp: datetime
    created_at: datetime
    is_revoked: bool
    usuario_id: int

    class Config:
        from_attributes = True

class ResetPasswordTokenCreateDTO(SQLModel):
    token: str
    exp: datetime
    usuario_id: int

    class Config:
        from_attributes = True