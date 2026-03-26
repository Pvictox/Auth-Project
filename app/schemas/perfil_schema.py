from pydantic import BaseModel


class PerfilBase(BaseModel):
    id_perfil: int
    valor: str


class PerfilPublic(BaseModel):
    valor: str


class PerfilFormData(PerfilPublic):
    pass
