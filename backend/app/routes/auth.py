## backend/app/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, TokenResponse
from app.services.auth_service import AuthService
from app.utils.jwt import verify_token
from app.services.logout_service import LogoutService
from app.utils.rate_limit import limiter
from app.models.user import User
from app.utils.dependencies import get_current_user, require_roles
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


@router.post("/users", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_user_with_role(
    user_create: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """
    Criar usuário com papel (role) livre: user, manager, supervisor ou admin.

    Protegido - só um admin autenticado pode chamar esta rota. Use este
    endpoint (em vez de /auth/register) sempre que precisar criar uma
    conta com privilégio acima de "user".
    """
    try:
        result = await AuthService.create_user_by_admin(db, user_create)
        return {"message": "Usuário criado com sucesso", **result}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Erro ao criar usuário: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao criar usuário",
        )


@router.get("/me", response_model=dict)
async def read_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """
    Obter informações do usuário autenticado.

    Antes, esta rota só decodificava o JWT e devolvia {"id", "email"}
    (o token nunca carregava full_name/username) - por isso o header do
    frontend sempre caia no fallback do e-mail, mesmo quando o usuário
    tinha um nome cadastrado. Agora busca o usuário completo no banco.
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "is_admin": current_user.is_admin,
    }


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    authorization: str = Header(None),
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