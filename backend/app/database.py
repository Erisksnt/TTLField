## backend/app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import event, pool, text
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)

settings = get_settings()

# Converter postgresql:// para postgresql+asyncpg://
database_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(
    database_url,
    echo=settings.debug,
    future=True,
    pool_pre_ping=True,
    pool_recycle=3600,
    poolclass=pool.NullPool,
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


async def check_db_connection(max_retries: int = 5, retry_delay: int = 2) -> bool:
    """
    Verificar se o banco de dados está disponível com retry automático
    """
    import asyncio
    
    for attempt in range(1, max_retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info(f"✅ Banco de dados conectado com sucesso (tentativa {attempt}/{max_retries})")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Tentativa {attempt}/{max_retries} falhou: {str(e)}")
            if attempt < max_retries:
                await asyncio.sleep(retry_delay)
            else:
                logger.error(f"❌ Falha ao conectar ao banco após {max_retries} tentativas")
                return False
    return False


async def init_db() -> None:
    """
    Inicializar banco de dados criando todas as tabelas
    COM VALIDAÇÃO DE CONEXÃO
    """
    logger.info("Verificando conexão com o banco de dados...")
    
    is_connected = await check_db_connection()
    
    if not is_connected:
        raise ConnectionError(
            "Não foi possível conectar ao PostgreSQL. "
            "Verifique se o serviço está rodando: docker-compose up -d postgres"
        )
    
    logger.info("Criando tabelas no banco de dados...")
    
    # Importar modelos AQUI para evitar circular import
    from app.models.user import User
    from app.models.technician import Technician
    from app.models.position import Position
    from app.models.geofence import Geofence
    from app.models.alert import Alert
    from app.models.device import Device
    from app.models.event import Event
    from app.models.token_blacklist import TokenBlacklist
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("✅ Banco de dados inicializado com sucesso")


async def close_db() -> None:
    """Fechar conexão com banco de dados"""
    logger.info("Fechando conexão com o banco de dados...")
    await engine.dispose()
    logger.info("✅ Conexão fechada")