## backend/app/utils/rate_limit.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

# Configurar limiter baseado no IP
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])


def setup_rate_limit(app: FastAPI):
    """
    Configurar rate limiting na aplicação
    """
    # Registrar handler de erro específico
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    logger.info("✅ Rate limiting configurado")


# Limites específicos por endpoint
LOGIN_LIMIT = "5/minute"      # Máximo 5 tentativas de login por minuto
REGISTER_LIMIT = "3/hour"     # Máximo 3 registros por hora
API_LIMIT = "200/minute"      # Máximo 200 requisições por minuto
ADMIN_LIMIT = "500/minute"    # Máximo 500 requisições para admin