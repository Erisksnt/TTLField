from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import event, pool
from app.config import get_settings

settings = get_settings()

# Converter postgresql:// para postgresql+asyncpg://
database_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(
    database_url,
    echo=settings.debug,
    future=True,
    pool_pre_ping=True,
    pool_recycle=3600,
    poolclass=pool.NullPool,  # Para desenvolvimento, evita problemas de conexão
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

Base = declarative_base()


async def get_db() -> AsyncSession:
    """Dependency para obter sessão do banco de dados"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Inicializar banco de dados criando todas as tabelas"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Fechar conexão com banco de dados"""
    await engine.dispose()