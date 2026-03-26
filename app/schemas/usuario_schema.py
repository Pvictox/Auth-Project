from pydantic import BaseModel


class UsuarioBase(BaseModel):
    id_usuario: int
    nome: str
    is_active: bool
    uid: str
    email: str
    perfil_id: int


class UsuarioBaseResponse(UsuarioBase):
    pass


class UsuarioFormData(BaseModel):
    """
    Schema for receiving usuario data from form submissions, including password field.
    """

    nome: str
    uid: str
    email: str
    perfil: str
    ativo: bool = True
    password: str | None = None


class UsuarioDeleteFormData(BaseModel):
    """
    Schema for receiving usuario deletion data from form submissions.
    """

    uid: str
    email: str
    perfil: str
    is_active: bool
    nome: str


class UsuarioResetSenhaFormData(BaseModel):
    """
    Schema for receiving password reset data from form submissions.
    """

    token: str  # The reset token sent to the user's email
    new_password: str
