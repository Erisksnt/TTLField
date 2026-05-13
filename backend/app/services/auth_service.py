from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, TokenResponse
from app.utils.security import hash_password, verify_password
from app.utils.jwt import create_access_token, create_refresh_token
from app.config import get_settings
from fastapi import HTTPException, status
from datetime import timedelta

settings = get_settings()


class AuthService:
    @staticmethod
    async def register(db: AsyncSession, user_create: UserCreate) -> dict:
        """Registrar novo usuário"""
        # Verificar se usuário já existe
        stmt = select(User).where(
            (User.email == user_create.email) | (User.username == user_create.username)
        )
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email ou username já cadastrado",
            )
        
        # Criar novo usuário
        hashed_password = hash_password(user_create.password)
        db_user = User(
            email=user_create.email,
            username=user_create.username,
            hashed_password=hashed_password,
            full_name=user_create.full_name,
            role=user_create.role,
        )
        
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        
        return {"id": db_user.id, "email": db_user.email}

    @staticmethod
    async def login(db: AsyncSession, credentials: UserLogin) -> TokenResponse:
        """Fazer login e gerar tokens"""
        # Buscar usuário
        stmt = select(User).where(User.email == credentials.email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou senha inválidos",
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário inativo",
            )
        
        # Gerar tokens
        access_token = create_access_token(data={"sub": user.id, "email": user.email})
        refresh_token = create_refresh_token(data={"sub": user.id})
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
        )

    @staticmethod
    async def refresh_access_token(db: AsyncSession, user_id: str) -> TokenResponse:
        """Gerar novo access token usando refresh token"""
        # Buscar usuário
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário não encontrado ou inativo",
            )
        
        # Gerar novo access token
        access_token = create_access_token(data={"sub": user.id, "email": user.email})
        refresh_token = create_refresh_token(data={"sub": user.id})
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
        )