from fastapi import Depends, HTTPException, status

from app.core.security import get_current_user
from app.dto import TokenAuthenticatedDataDTO


class RolesChecker:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(
        self, user_token: TokenAuthenticatedDataDTO = Depends(get_current_user)
    ):
        if user_token.user.perfil not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted for your role.",
            )
