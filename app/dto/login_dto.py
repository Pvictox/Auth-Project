from pydantic import BaseModel


class LoginRequestDTO(BaseModel):
    """
    DTO for login request data.
    """

    uid: str
    password: str
