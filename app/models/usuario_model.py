from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models import PerfilModel, ResetPasswordTokenModel, TokenModel


class UsuarioModel(SQLModel, table=True):
    __tablename__: str = "usuario"
    __table_args__ = {"schema": "auth"}

    id_usuario: int = Field(default=None, primary_key=True)
    nome: str = Field(nullable=False)
    uid: str = Field(nullable=False, unique=True, index=True)
    email: str = Field(nullable=False, unique=True, index=True)
    is_active: bool = Field(default=True, nullable=False)
    hashed_pass: str = Field(nullable=False, unique=False)

    # Foreign key to PerfilModel
    perfil_id: int = Field(
        default=None, foreign_key="auth.perfis.id_perfil", nullable=False
    )

    # Relationships
    perfil: "PerfilModel" = Relationship(back_populates="usuarios")
    tokens: list["TokenModel"] = Relationship(back_populates="usuario")
    password_reset_tokens: list["ResetPasswordTokenModel"] = Relationship(
        back_populates="usuario"
    )
