from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, field_validator
from sqlmodel import SQLModel

from app.dto.perfil_dto import PerfilModelDTO

if TYPE_CHECKING:
    from app.dto.token_dto import TokenModelDTO


class UsuarioModelDTO(SQLModel):
    """
    DTO for the UsuarioModel, including related Perfil and Tokens.
    """

    id_usuario: int
    nome: str
    uid: str
    email: str
    is_active: bool
    perfil_id: int
    hashed_pass: str
    perfil: PerfilModelDTO
    tokens: list[TokenModelDTO] = []

    class Config:
        from_attributes = True


class UsuarioTokenDTO(BaseModel):
    """
    DTO of Usuario that will be used in the token payload, containing only essential information.
    """

    nome: str
    is_active: bool
    uid: str
    email: str
    perfil: str

    @field_validator("perfil", mode="before")
    @classmethod
    def extract_perfil_valor(cls, value):
        if isinstance(value, dict):
            return value.get("valor", "")
        elif isinstance(value, str):
            return value
        else:
            raise ValueError(
                "Invalid type for perfil field. Expected PerfilModelDTO or str."
            )


class UsuarioPublicDTO(UsuarioTokenDTO):
    """
    DTO for public representation of Usuario, inheriting from UsuarioTokenDTO.
    """
