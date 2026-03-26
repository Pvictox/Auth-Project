from pydantic import BaseModel

from app.dto import UsuarioPublicDTO


class LoginRequest(BaseModel):
    """
    Schema for login request data.
    """

    uid: str
    password: str


class SucessfulLoginResponse(BaseModel):
    """
    Base schema for successful login response, containing the access token and user information.
    """

    success: bool = True
    user: UsuarioPublicDTO


class LogoutResponse(BaseModel):
    success: bool = True
    message: str = "Logout successful"
