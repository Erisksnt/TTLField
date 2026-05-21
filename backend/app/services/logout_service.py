## backend/app/services/logout_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.token_blacklist import TokenBlacklist
from app.utils.jwt import verify_token
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class LogoutService:
    @staticmethod
    async def revoke_token(db: AsyncSession, token: str) -> bool:
        """
        Revogar um token (adicionar à blacklist)
        """
        # Verificar se token é válido
        payload = verify_token(token)
        if not payload:
            return False
        
        # Obter expiração do token
        exp = payload.get("exp")
        expires_at = datetime.fromtimestamp(exp) if exp else None
        
        # Adicionar à blacklist
        blacklisted = TokenBlacklist(
            token=token,
            expires_at=expires_at
        )
        db.add(blacklisted)
        await db.commit()
        
        logger.info(f"Token revogado com sucesso")
        return True
    
    @staticmethod
    async def is_token_revoked(db: AsyncSession, token: str) -> bool:
        """
        Verificar se um token está na blacklist
        """
        stmt = select(TokenBlacklist).where(TokenBlacklist.token == token)
        result = await db.execute(stmt)
        return result.scalar_one_or_none() is not None
    
    @staticmethod
    async def cleanup_expired_tokens(db: AsyncSession):
        """
        Remover tokens expirados da blacklist (manutenção)
        """
        stmt = delete(TokenBlacklist).where(
            TokenBlacklist.expires_at < datetime.utcnow()
        )
        result = await db.execute(stmt)
        await db.commit()
        logger.info(f"Removidos {result.rowcount} tokens expirados da blacklist")