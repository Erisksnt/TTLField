## backend/seed.py
import asyncio
import logging
import os
import re
import sys
import uuid

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.future import select

from app.models import User
from app.utils.security import hash_password
from app.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


def _validate_password(password: str) -> None:
    if len(password) < 8:
        raise ValueError("SEED_ADMIN_PASSWORD deve ter pelo menos 8 caracteres")
    if not re.search(r"[A-Z]", password):
        raise ValueError("SEED_ADMIN_PASSWORD deve conter pelo menos uma letra maiuscula")
    if not re.search(r"[a-z]", password):
        raise ValueError("SEED_ADMIN_PASSWORD deve conter pelo menos uma letra minuscula")
    if not re.search(r"[0-9]", password):
        raise ValueError("SEED_ADMIN_PASSWORD deve conter pelo menos um numero")


def _load_admin_config() -> dict:
    email = os.getenv("SEED_ADMIN_EMAIL")
    username = os.getenv("SEED_ADMIN_USERNAME")
    password = os.getenv("SEED_ADMIN_PASSWORD")
    full_name = os.getenv("SEED_ADMIN_FULL_NAME", "Administrator")

    missing = [
        name for name, value in [
            ("SEED_ADMIN_EMAIL", email),
            ("SEED_ADMIN_USERNAME", username),
            ("SEED_ADMIN_PASSWORD", password),
        ]
        if not value
    ]
    if missing:
        raise ValueError(
            "As seguintes variaveis de ambiente sao obrigatorias e nao foram "
            f"definidas: {', '.join(missing)}. Defina-as no .env ou via "
            "export antes de rodar 'python seed.py'."
        )

    _validate_password(password)

    return {
        "email": email,
        "username": username,
        "password": password,
        "full_name": full_name,
    }


async def seed_admin_user():
    admin_config = _load_admin_config()

    engine = create_async_engine(
        settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
        echo=False,
    )

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        stmt = select(User).where(
            (User.email == admin_config["email"]) | (User.username == admin_config["username"])
        )
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            logger.info(
                "Usuario com esse email/username ja existe (id=%s) - nada a fazer.",
                existing.id,
            )
            return

        admin_user = User(
            id=str(uuid.uuid4()),
            email=admin_config["email"],
            username=admin_config["username"],
            hashed_password=hash_password(admin_config["password"]),
            full_name=admin_config["full_name"],
            role="admin",
            is_active=True,
            is_admin=True,
        )

        session.add(admin_user)
        await session.commit()

        logger.info("Usuario admin criado com sucesso: %s", admin_config["email"])


if __name__ == "__main__":
    try:
        asyncio.run(seed_admin_user())
    except ValueError as e:
        logger.error("❌ %s", e)
        sys.exit(1)