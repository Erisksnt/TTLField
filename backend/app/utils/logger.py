## backend/app/utils/logger.py
import logging
import sys
from app.config import get_settings

settings = get_settings()


def setup_logger(name: str = "isp_tracker") -> logging.Logger:
    """
    Configurar logger estruturado para a aplicação
    """
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    log_level = logging.DEBUG if settings.debug else logging.INFO
    logger.setLevel(log_level)
    
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Obter logger configurado para um módulo específico
    """
    return logging.getLogger(f"isp_tracker.{name}")