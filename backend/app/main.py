from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import logging
import traceback
import asyncio

from app.config import get_settings
from app.database import init_db, close_db, get_db
from app.routes import auth, technicians, positions, geofences, websocket, reports, geofence_events
from app.services.logout_service import LogoutService
from app.utils.rate_limit import setup_rate_limit, limiter
from app.services.geofence_service import start_periodic_check


# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerenciar startup e shutdown da aplicação"""
    # Startup
    logger.info("Inicializando aplicação...")
    try:
        await init_db()
        logger.info("✅ Banco de dados inicializado com sucesso")
    except ConnectionError as e:
        logger.error(f"❌ Falha crítica na inicialização: {str(e)}")
        raise

    # ============================================
    # TAREFA PERIÓDICA DE SINCRONIZAÇÃO COM TRACCAR
    # ============================================
    async def sync_positions():
        while True:
            try:
                from app.services.tracking_service import update_all_technicians_positions
                await update_all_technicians_positions()
            except Exception as e:
                logger.error(f"Erro na sincronização de posições: {e}")
            await asyncio.sleep(30)  # a cada 30 segundos

    sync_task = asyncio.create_task(sync_positions())

    # ============================================
    # TAREFA PERIÓDICA DE VERIFICAÇÃO DE GEOFENCES (a cada 60 segundos)
    # ============================================
    geofence_check_task = asyncio.create_task(start_periodic_check(interval_seconds=60))

    yield

    # Shutdown
    logger.info("Finalizando aplicação...")
    sync_task.cancel()
    geofence_check_task.cancel()
    try:
        await sync_task
        await geofence_check_task
    except asyncio.CancelledError:
        pass
    await close_db()
    logger.info("✅ Conexão com banco de dados fechada")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Platform de rastreamento e inteligência operacional para ISP",
    lifespan=lifespan,
)

# Configurar Rate Limiting
setup_rate_limit(app)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)


# ============================================
# MIDDLEWARE PARA VERIFICAR TOKEN REVOGADO
# ============================================
@app.middleware("http")
async def check_blacklisted_token(request: Request, call_next):
    public_paths = ["/auth/login", "/auth/register", "/health", "/docs", "/openapi.json", "/"]
    if request.url.path in public_paths:
        return await call_next(request)

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        async for db in get_db():
            if await LogoutService.is_token_revoked(db, token):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Token revogado - faça login novamente", "type": "token_revoked"}
                )
            break

    return await call_next(request)


# Health check
@app.get("/health", tags=["health"])
async def health_check():
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
    }


# API Routes
@app.get("/", tags=["root"])
async def root():
    return {
        "message": f"Bem-vindo ao {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
    }


# Registrar rotas
app.include_router(auth.router)
app.include_router(technicians.router)
app.include_router(positions.router)
app.include_router(geofences.router)
app.include_router(websocket.router)
app.include_router(reports.router)
app.include_router(geofence_events.router)


# ============================================
# HANDLERS DE ERRO
# ============================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTP Exception {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "type": "http_error"},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Erro de validação: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "type": "validation_error"},
    )


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Erro no banco de dados: {str(exc)}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erro interno no banco de dados", "type": "database_error"},
    )


@app.exception_handler(IntegrityError)
async def integrity_exception_handler(request: Request, exc: IntegrityError):
    logger.error(f"Erro de integridade: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Conflito de dados - recurso já existe", "type": "integrity_error"},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Erro não tratado: {str(exc)}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno do servidor", "type": "internal_error"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )