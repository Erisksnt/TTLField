## backend/app/services/websocket_manager.py
from fastapi import WebSocket
from typing import Dict, List, Set
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Gerencia conexões WebSocket ativas"""
    
    def __init__(self):
        # Clientes conectados: {client_id: websocket}
        self.active_connections: Dict[str, WebSocket] = {}
        # Técnicos conectados: {technician_id: websocket}
        self.technician_connections: Dict[str, WebSocket] = {}
        # Frontends conectados: {frontend_id: websocket}
        self.frontend_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_type: str, client_id: str):
        """Aceitar nova conexão WebSocket"""
        await websocket.accept()
        
        if client_type == "technician":
            self.technician_connections[client_id] = websocket
        elif client_type == "frontend":
            self.frontend_connections[client_id] = websocket
        else:
            self.active_connections[client_id] = websocket
        
        logger.info(f"✅ WebSocket conectado: {client_type}/{client_id}")
        logger.info(f"📊 Conexões ativas: Técnicos={len(self.technician_connections)}, Frontends={len(self.frontend_connections)}")
    
    def disconnect(self, client_type: str, client_id: str):
        """Remover conexão WebSocket"""
        if client_type == "technician":
            self.technician_connections.pop(client_id, None)
        elif client_type == "frontend":
            self.frontend_connections.pop(client_id, None)
        else:
            self.active_connections.pop(client_id, None)
        
        logger.info(f"❌ WebSocket desconectado: {client_type}/{client_id}")
    
    async def send_position_update(self, technician_id: str, position_data: dict):
        """Enviar atualização de posição para todos os frontends"""
        message = {
            "type": "position_update",
            "technician_id": technician_id,
            "data": position_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Enviar para todos os frontends conectados
        for frontend_id, connection in self.frontend_connections.items():
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Erro ao enviar para {frontend_id}: {e}")
    
    async def send_alert(self, alert_data: dict):
        """Enviar alerta para todos os frontends"""
        message = {
            "type": "alert",
            "data": alert_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for frontend_id, connection in self.frontend_connections.items():
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Erro ao enviar alerta: {e}")
    
    async def send_technician_status(self, technician_id: str, is_online: bool):
        """Enviar atualização de status online/offline"""
        message = {
            "type": "status_change",
            "technician_id": technician_id,
            "is_online": is_online,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for frontend_id, connection in self.frontend_connections.items():
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Erro ao enviar status: {e}")


# Instância global do gerenciador
manager = ConnectionManager()