from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.config import get_settings
from app.database import init_db, close_db
from app.routes import auth, technicians, positions

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerenciar startup e shutdown da aplicação"""
    # Startup
    logger.info("Inicializando aplicação...")
    await init_db()
    logger.info("Banco de dados inicializado")
    yield
    # Shutdown
    logger.info("Finalizando aplicação...")
    await close_db()
    logger.info("Conexão com banco de dados fechada")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Platform de rastreamento e inteligência operacional para ISP",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)


# Health check
@app.get("/health", tags=["health"])
async def health_check():
    """Verificar saúde da aplicação"""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
    }


# API Routes
@app.get("/", tags=["root"])
async def root():
    """API Root"""
    return {
        "message": f"Bem-vindo ao {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
    }


# Registrar rotas
app.include_router(auth.router)
app.include_router(technicians.router)
app.include_router(positions.router)


# Error handling
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Erro não tratado: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno do servidor"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )