from dataclasses import dataclass

from sqlmodel import SQLModel


@dataclass
class PerfilModelDTO(SQLModel):
    id_perfil: int
    valor: str

    class Config:
        from_attributes = True
