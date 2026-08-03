## backend/app/routes/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from app.services.websocket_manager import manager
from app.services.position_service import PositionService
from app.database import AsyncSessionLocal
from app.utils.dependencies import get_current_user_ws
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
    Endpoint WebSocket para comunicacao em tempo real

    client_type: "technician" ou "frontend"
    client_id: ID do tecnico ou frontend

    Requer um token JWT valido via query string (?token=...), ja que o
    navegador nao permite enviar um header Authorization customizado ao
    abrir uma conexao WebSocket. Sem isso, qualquer pessoa conseguia se
    conectar sem login e ler/injetar posicoes de GPS em tempo real.
    """
    # Autenticar ANTES de aceitar a conexao
    async with AsyncSessionLocal() as auth_db:
        user = await get_current_user_ws(websocket, auth_db)

    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        logger.warning(
            "Conexao WebSocket recusada (token ausente/invalido/revogado) - client_type=%s client_id=%s",
            client_type, client_id,
        )
        return

    await manager.connect(websocket, client_type, client_id)
    logger.info("WebSocket autenticado: user=%s client_type=%s client_id=%s", user.email, client_type, client_id)

    try:
        while True:
            # Aguardar mensagem do cliente
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                message_type = message.get("type")

                if client_type == "technician" and message_type == "position":
                    # Tecnico enviou posicao
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
                    # Heartbeat - manter conexao viva
                    await websocket.send_json({"type": "pong"})

                elif message_type == "status":
                    # Tecnico mudou status online/offline
                    is_online = message.get("is_online", False)
                    await manager.send_technician_status(client_id, is_online)

            except json.JSONDecodeError:
                logger.error(f"JSON invalido recebido: {data}")

    except WebSocketDisconnect:
        manager.disconnect(client_type, client_id)
        logger.info(f"Cliente desconectado: {client_type}/{client_id}")
