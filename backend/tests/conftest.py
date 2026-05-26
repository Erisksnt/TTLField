## backend/tests/conftest.py
import sys
import os
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Cliente de teste para FastAPI"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_token(client):
    """Fixture para obter token de autenticação"""
    import uuid
    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    username = f"user_{uuid.uuid4().hex[:8]}"
    password = "12345678"
    
    # Registrar (com delay para evitar rate limit)
    time.sleep(1)
    reg_response = client.post("/auth/register", json={
        "email": unique_email,
        "username": username,
        "password": password
    })
    
    if reg_response.status_code != 201:
        # Se falhar por rate limit, esperar mais e tentar novamente
        time.sleep(3)
        unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        username = f"user_{uuid.uuid4().hex[:8]}"
        reg_response = client.post("/auth/register", json={
            "email": unique_email,
            "username": username,
            "password": password
        })
    
    assert reg_response.status_code == 201, f"Registro falhou: {reg_response.status_code}"
    
    # Login com delay
    time.sleep(1)
    login_response = client.post("/auth/login", json={
        "email": unique_email,
        "password": password
    })
    
    assert login_response.status_code == 200, f"Login falhou: {login_response.status_code} - {login_response.text}"
    return login_response.json().get("access_token")