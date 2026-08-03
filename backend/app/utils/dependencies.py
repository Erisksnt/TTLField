## backend/app/utils/dependencies.py
"""
Dependências de autenticação e autorização reutilizáveis em todas as rotas.

Contexto: antes desta implementação, o JWT era emitido no login mas
NUNCA era exigido nas rotas de negócio (technicians, positions,
geofences, reports, geofence_events, websocket) - o middleware global
em app/main.py só invalidava um token se ele fosse enviado e estivesse
revogado, mas não obrigava que nenhum token fosse enviado. Ou seja,
qualquer requisição sem header Authorization passava direto.

Este módulo centraliza a checagem real de autenticação (get_current_user)
e de autorização por papel (require_roles), para serem usados via
Depends(...) em cada rota que precisa de proteção.
"""
import logging
from typing import Optional

from fastapi import Depends, Header, HTTPException, WebSocket, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.logout_service import LogoutService
from app.utils.jwt import verify_token

logger = logging.getLogger(__name__)


def _extract_bearer_token(authorization: Optional[str]) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return authorization.split(" ", 1)[1]


async def get_current_user(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependência padrão para proteger rotas HTTP.

    - Exige header `Authorization: Bearer <token>`.
    - Valida assinatura e expiração do JWT.
    - Rejeita refresh tokens usados como access token.
    - Garante que o token não foi revogado (blacklist de logout).
    - Carrega o usuário do banco e garante que está ativo.

    Uso: `current_user: User = Depends(get_current_user)`
    """
    token = _extract_bearer_token(authorization)

    payload = verify_token(token)
    if not payload or payload.get("type") == "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        )

    if await LogoutService.is_token_revoked(db, token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token revogado - faça login novamente",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado ou inativo",
        )

    return user


def require_roles(*allowed_roles: str):
    """
    Factory de dependência para restringir uma rota a papéis específicos.

    Uso: `current_user: User = Depends(require_roles("admin", "manager"))`

    Usuários com `is_admin=True` sempre passam, independente do `role`.
    """
    allowed = set(allowed_roles)

    async def _checker(user: User = Depends(get_current_user)) -> User:
        if user.is_admin or user.role in allowed:
            return user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para executar esta ação",
        )

    return _checker


async def get_current_user_ws(websocket: WebSocket, db: AsyncSession) -> Optional[User]:
    """
    Autenticação para conexões WebSocket.

    O token é lido via query string (`?token=...`) porque o navegador
    não permite enviar header Authorization customizado ao abrir um
    WebSocket. Retorna None se o token estiver ausente/inválido/revogado
    - quem chama decide como reagir (normalmente fechar a conexão).
    """
    token = websocket.query_params.get("token")
    if not token:
        return None

    payload = verify_token(token)
    if not payload or payload.get("type") == "refresh":
        return None

    if await LogoutService.is_token_revoked(db, token):
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        return None

    return user
