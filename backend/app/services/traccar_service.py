import httpx
import logging
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class TraccarService:
    def __init__(self):
        self.base_url = settings.traccar_url
        self.api_url = f"{self.base_url}/api"
        self.username = settings.traccar_admin_user
        self.password = settings.traccar_admin_password
        self.session_cookie = None
    
    async def authenticate(self) -> bool:
        """Autenticar no Traccar usando form-data"""
        async with httpx.AsyncClient() as client:
            data = {
                "email": self.username,
                "password": self.password
            }
            response = await client.post(
                f"{self.api_url}/session",
                data=data
            )
            
            if response.status_code == 200:
                self.session_cookie = response.cookies.get("JSESSIONID")
                logger.info(f"✅ Autenticado no Traccar")
                return True
            else:
                logger.error(f"❌ Erro ao autenticar: {response.status_code}")
                return False
    
    async def create_device(self, name: str, unique_id: str) -> dict:
        """Criar dispositivo no Traccar"""
        if not self.session_cookie:
            await self.authenticate()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/devices",
                json={
                    "name": name,
                    "uniqueId": unique_id,
                    "status": "online"
                },
                cookies={"JSESSIONID": self.session_cookie}
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Dispositivo criado: {name} (ID: {unique_id})")
                return response.json()
            else:
                logger.error(f"❌ Erro ao criar dispositivo: {response.text}")
                return None
    
    async def delete_device(self, device_id: str) -> bool:
        """Deletar dispositivo no Traccar"""
        if not self.session_cookie:
            await self.authenticate()
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.api_url}/devices/{device_id}",
                cookies={"JSESSIONID": self.session_cookie}
            )
            
            if response.status_code == 204:
                logger.info(f"✅ Dispositivo deletado no Traccar: {device_id}")
                return True
            else:
                logger.error(f"❌ Erro ao deletar dispositivo: {response.status_code} - {response.text}")
                return False

    async def get_device_by_unique_id(self, unique_id: str) -> dict | None:
        """Busca um dispositivo no Traccar pelo uniqueId."""
        if not self.session_cookie:
            await self.authenticate()
    
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/devices",
                cookies={"JSESSIONID": self.session_cookie}
            )
            if response.status_code == 200:
                devices = response.json()
                for device in devices:
                    if device.get("uniqueId") == unique_id:
                        return device
            return None

    async def get_all_devices(self) -> list:
        """Retorna todos os dispositivos do Traccar."""
        if not self.session_cookie:
            await self.authenticate()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/devices",
                cookies={"JSESSIONID": self.session_cookie}
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Erro ao buscar dispositivos: {response.status_code}")
                return []