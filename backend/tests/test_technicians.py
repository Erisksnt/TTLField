## backend/tests/test_technicians.py
import pytest
import uuid


class TestTechnicians:
    
    def test_create_technician_success(self, client, auth_token):
        """Teste: Criar técnico com sucesso"""
        unique_id = uuid.uuid4().hex[:8]
        response = client.post("/technicians", 
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "João Silva",
                "employee_id": f"EMP{unique_id}",
                "email": f"joao_{unique_id}@isp.com",
                "phone": "(11) 99999-9999"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "João Silva"
        assert "EMP" in data["employee_id"]
    
    def test_create_technician_duplicate(self, client, auth_token):
        """Teste: Criar técnico com employee_id duplicado deve falhar"""
        unique_id = uuid.uuid4().hex[:8]
        employee_id = f"EMP{unique_id}"
        
        # Primeiro técnico
        client.post("/technicians", 
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "João Silva",
                "employee_id": employee_id,
                "email": f"joao_{unique_id}@isp.com"
            }
        )
        
        # Segundo técnico com mesmo employee_id
        response = client.post("/technicians", 
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Maria Silva",
                "employee_id": employee_id,
                "email": f"maria_{unique_id}@isp.com"
            }
        )
        assert response.status_code == 400
    
    def test_list_technicians(self, client, auth_token):
        """Teste: Listar técnicos"""
        response = client.get("/technicians",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)