from pydantic import BaseModel

from app.dto.usuario_DTO import UsuarioPublicDTO

class UsuarioBase(BaseModel):
    id_usuario: int
    nome: str
    is_active: bool
    uid: str
    email: str
    perfil_id: int

class UsuarioBaseResponse(UsuarioBase):
    pass

class UsuarioCreateResponse(BaseModel):
    sucess: bool
    user: UsuarioPublicDTO 
class UsuarioFormData(BaseModel):
    '''
    Schema for receiving usuario data from form submissions, including password field.
    '''
    nome: str
    uid: str
    email: str
    perfil: str
    ativo: bool = True
    password: str

class UsuarioResetSenhaFormData(BaseModel):
    '''
    Schema for receiving password reset data from form submissions.
    '''
    token: str # The reset token sent to the user's email
    new_password: str
    