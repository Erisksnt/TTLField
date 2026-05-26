## backend/app/utils/rate_limit.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging
import sys

logger = logging.getLogger(__name__)

# Detectar se está rodando testes
IS_TESTING = "pytest" in sys.modules

if IS_TESTING:
    # Desabilitar rate limit completamente durante testes
    limiter = Limiter(key_func=get_remote_address, default_limits=["1000000/minute"])
    LOGIN_LIMIT = "1000000/minute"
    REGISTER_LIMIT = "1000000/hour"
    logger.info("🔧 Rate limit desabilitado para testes")
else:
    limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
    LOGIN_LIMIT = "5/minute"
    REGISTER_LIMIT = "3/hour"
    logger.info("✅ Rate limiting configurado")


def setup_rate_limit(app: FastAPI):
    """Configurar rate limiting na aplicação"""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    logger.info("✅ Setup rate limiting concluído")


API_LIMIT = "200/minute"
ADMIN_LIMIT = "500/minute"