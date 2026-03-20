
from fastapi import APIRouter, Depends, status, HTTPException, Form, Response, Request
from app.database import get_session

from app.schemas.login_schema import LoginRequest, SucessfulLoginResponse, LogoutResponse
from app.dto import LoginRequestDTO, TokenAuthenticatedDataDTO, UsuarioPublicDTO
from typing import Annotated
from app.services.auth_service import AuthService
from sqlmodel import Session
from app.log_config.logging_config import get_logger

from app.core.security import (
    get_current_user,
)

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={404: {"description": "Not found"}},
)

logger = get_logger(__name__)

SessionDependency = Annotated[ Session, Depends(get_session) ]


@router.post("/login",tags=["authentication"], status_code=status.HTTP_200_OK, response_model=SucessfulLoginResponse)
async def login(login_data: Annotated[LoginRequest, Form()], session: SessionDependency, response:Response) -> SucessfulLoginResponse | None:
    try:
        auth_service = AuthService(session=session)
        login_data_dto = LoginRequestDTO(**login_data.model_dump())
        token_response = auth_service.handle_login(data=login_data_dto, response=response)
        
        if not token_response:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid UID or password")
        
        return token_response
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed.")
    
    
@router.post("/refresh", tags=["authentication"], status_code=status.HTTP_200_OK, response_model=SucessfulLoginResponse)
async def refresh_token(session: SessionDependency, 
                        response: Response,
                        request: Request) -> SucessfulLoginResponse | None:
    try:
        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            logger.warning("Refresh token is missing in the request cookies.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Refresh token is missing")
        
        auth_service = AuthService(session=session)
        logger.warning(f"Received refresh token: {refresh_token}")
        token_response = auth_service.refresh_acess_token(refresh_token=refresh_token, response=response)
        
        if not token_response:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        
        return token_response
    except HTTPException as http_exc:
        logger.error(f"HTTPException during token refresh: {http_exc.detail}")
        raise http_exc

#TODO: This is really responsability of this endpoint? Maybe it should be in a separate router or even put it on Usuarios?
@router.post("/forgot-password", tags=["authentication"], status_code=status.HTTP_200_OK)
async def forgot_password(email: Annotated[str, Form()], session: SessionDependency) -> dict:
    auth_service = AuthService(session=session)
    return await auth_service.forgot_password(email=email)

@router.post("/logout", tags=["authentication"], status_code=status.HTTP_200_OK, response_model=LogoutResponse)
async def logout(response:Response, 
                session: SessionDependency,
                current_user: Annotated[TokenAuthenticatedDataDTO, Depends(get_current_user)],
                request: Request) -> LogoutResponse:
    
    try:
        if not current_user: 
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
        
        refresh_token = request.cookies.get("refresh_token")
        auth_service = AuthService(session=session)
        logout_response = auth_service.logout(refresh_token=refresh_token, response=response)
        
        return logout_response
    except HTTPException as http_exc:
        raise http_exc

@router.get("/me", tags=["authentication"], status_code=status.HTTP_200_OK, response_model=SucessfulLoginResponse)
async def fetch_current_user(current_user = Depends(get_current_user)) -> SucessfulLoginResponse:
    logger.warning(f"Current user data: {current_user}")
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    
    return SucessfulLoginResponse(
        success=True,
        user= UsuarioPublicDTO(**current_user.user.model_dump())
    )