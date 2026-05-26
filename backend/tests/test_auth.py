## backend/tests/test_auth.py
import pytest
import uuid
import time


class TestAuth:
    
    def test_register_success(self, client):
        """Teste: Registrar novo usuário com sucesso"""
        unique_email = f"novo_{uuid.uuid4().hex[:8]}@example.com"
        response = client.post("/auth/register", json={
            "email": unique_email,
            "username": f"novouser_{uuid.uuid4().hex[:8]}",
            "password": "12345678",
            "full_name": "Novo Usuário"
        })
        assert response.status_code == 201
        data = response.json()
        assert "user_id" in data
    
    def test_register_duplicate_email(self, client):
        """Teste: Registrar com email duplicado deve falhar"""
        unique_email = f"duplicado_{uuid.uuid4().hex[:8]}@example.com"
        username = f"user_{uuid.uuid4().hex[:8]}"
        
        # Primeiro registro
        client.post("/auth/register", json={
            "email": unique_email,
            "username": username,
            "password": "12345678"
        })
        
        # Segundo registro com mesmo email
        response = client.post("/auth/register", json={
            "email": unique_email,
            "username": f"user2_{uuid.uuid4().hex[:8]}",
            "password": "12345678"
        })
        assert response.status_code == 400
    
    def test_login_success(self, client):
        """Teste: Login com credenciais corretas"""
        unique_email = f"logintest_{uuid.uuid4().hex[:8]}@example.com"
        username = f"logintest_{uuid.uuid4().hex[:8]}"
        password = "senha123"
        
        # Criar usuário
        reg_response = client.post("/auth/register", json={
            "email": unique_email,
            "username": username,
            "password": password
        })
        
        # Verificar se registro foi bem sucedido
        if reg_response.status_code != 201:
            # Se falhou por rate limit, esperar um pouco
            time.sleep(2)
            # Tentar novamente com dados diferentes
            unique_email = f"logintest2_{uuid.uuid4().hex[:8]}@example.com"
            username = f"logintest2_{uuid.uuid4().hex[:8]}"
            client.post("/auth/register", json={
                "email": unique_email,
                "username": username,
                "password": password
            })
        
        # Login
        response = client.post("/auth/login", json={
            "email": unique_email,
            "password": password
        })
        
        # Se ainda falhar, mostrar detalhes
        if response.status_code != 200:
            print(f"Login falhou: {response.status_code} - {response.text}")
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_login_wrong_password(self, client):
        """Teste: Login com senha errada deve falhar"""
        unique_email = f"senhaerrada_{uuid.uuid4().hex[:8]}@example.com"
        username = f"senhaerrada_{uuid.uuid4().hex[:8]}"
        
        # Criar usuário
        client.post("/auth/register", json={
            "email": unique_email,
            "username": username,
            "password": "senha123"
        })
        
        # Login com senha errada
        response = client.post("/auth/login", json={
            "email": unique_email,
            "password": "senha_errada"
        })
        assert response.status_code == 401
    
    def test_logout_success(self, client):
        """Teste: Logout deve funcionar"""
        unique_email = f"logout_{uuid.uuid4().hex[:8]}@example.com"
        username = f"logout_{uuid.uuid4().hex[:8]}"
        password = "senha123"
        
        # Criar usuário
        client.post("/auth/register", json={
            "email": unique_email,
            "username": username,
            "password": password
        })
        
        # Fazer login
        login_response = client.post("/auth/login", json={
            "email": unique_email,
            "password": password
        })
        
        # Verificar se login foi bem sucedido
        if login_response.status_code != 200:
            # Tentar novamente
            time.sleep(2)
            login_response = client.post("/auth/login", json={
                "email": unique_email,
                "password": password
            })
        
        assert login_response.status_code == 200, f"Login falhou: {login_response.status_code}"
        
        token = login_response.json().get("access_token")
        assert token is not None, "Token não encontrado na resposta"
        
        # Logout
        response = client.post("/auth/logout", 
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert "Logout realizado" in response.json()["message"]

    def test_login_success(self, client, auth_token):
        """Teste: Login com credenciais corretas"""
        # O auth_token já contém um token válido
        # Vamos extrair o email do usuário logado
        import jwt
        token = auth_token
        
        # Decodificar token para pegar o email
        payload = jwt.decode(token, options={"verify_signature": False})
        email = payload.get("email")
        
        # Fazer login com o mesmo usuário
        response = client.post("/auth/login", json={
            "email": email,
            "password": "12345678"  # Senha usada no fixture
        })
        assert response.status_code == 200
        assert "access_token" in response.json()
    