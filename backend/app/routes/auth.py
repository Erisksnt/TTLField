## backend/app/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, TokenResponse
from app.services.auth_service import AuthService
from app.utils.jwt import get_user_from_token, verify_token
from app.services.logout_service import LogoutService
from app.utils.rate_limit import limiter
import logging

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/hour")
async def register(
    request: Request,
    user_create: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Registrar novo usuário administrativo"""
    try:
        result = await AuthService.register(db, user_create)
        return {"message": "Usuário registrado com sucesso", "user_id": result["id"]}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Erro ao registrar usuário: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao registrar usuário",
        )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """Fazer login e obter tokens"""
    try:
        tokens = await AuthService.login(db, credentials)
        return tokens
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Erro ao fazer login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao fazer login",
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db),
):
    """Renovar access token usando refresh token"""
    try:
        payload = verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
            )
        
        user_id = payload.get("sub")
        tokens = await AuthService.refresh_access_token(db, user_id)
        return tokens
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Erro ao renovar token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Erro ao renovar token",
        )


@router.get("/me", response_model=dict)
async def get_current_user(
    authorization: str = None,
):
    """Obter informações do usuário autenticado"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido",
        )
    
    token = authorization.split(" ")[1]
    user = get_user_from_token(token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )
    
    return user


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    authorization: str = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Fazer logout (revogar token atual)
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido",
        )
    
    token = authorization.split(" ")[1]
    
    # Revogar token
    success = await LogoutService.revoke_token(db, token)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )
    
    return {"message": "Logout realizado com sucesso"}