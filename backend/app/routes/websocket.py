## backend/app/routes/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.websocket_manager import manager
from app.services.position_service import PositionService
from app.database import AsyncSessionLocal
import logging
import json

router = APIRouter(tags=["websocket"])
logger = logging.getLogger(__name__)


@router.websocket("/ws/{client_type}/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_type: str,
    client_id: str
):
    """
    Endpoint WebSocket para comunicação em tempo real
    
    client_type: "technician" ou "frontend"
    client_id: ID do técnico ou frontend
    """
    await manager.connect(websocket, client_type, client_id)
    
    try:
        while True:
            # Aguardar mensagem do cliente
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if client_type == "technician" and message_type == "position":
                    # Técnico enviou posição
                    position_data = message.get("data", {})
                    
                    # Salvar no banco de dados
                    async with AsyncSessionLocal() as db:
                        position_service = PositionService(db)
                        await position_service.save_position(
                            technician_id=client_id,
                            **position_data
                        )
                    
                    # Broadcast para todos os frontends
                    await manager.send_position_update(client_id, position_data)
                
                elif message_type == "ping":
                    # Heartbeat - manter conexão viva
                    await websocket.send_json({"type": "pong"})
                
                elif message_type == "status":
                    # Técnico mudou status online/offline
                    is_online = message.get("is_online", False)
                    await manager.send_technician_status(client_id, is_online)
                
            except json.JSONDecodeError:
                logger.error(f"JSON inválido recebido: {data}")
                
    except WebSocketDisconnect:
        manager.disconnect(client_type, client_id)
        logger.info(f"Cliente desconectado: {client_type}/{client_id}")