from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.position import PositionCreate, PositionResponse, PositionBulkCreate
from app.services.tracking_service import TrackingService
import logging

router = APIRouter(prefix="/positions", tags=["tracking"])
logger = logging.getLogger(__name__)


@router.post("", response_model=PositionResponse, status_code=status.HTTP_201_CREATED)
async def create_position(
    technician_id: str,
    device_id: str,
    position: PositionCreate,
    db: AsyncSession = Depends(get_db),
):
    """Criar nova posição (enviada pelo app mobile)"""
    try:
        db_position = await TrackingService.create_position(
            db, technician_id, device_id, position
        )
        return PositionResponse.model_validate(db_position)
    except Exception as e:
        logger.error(f"Erro ao criar posição: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao salvar posição",
        )


@router.post("/bulk", status_code=status.HTTP_201_CREATED)
async def create_positions_bulk(
    technician_id: str,
    device_id: str,
    bulk: PositionBulkCreate,
    db: AsyncSession = Depends(get_db),
):
    """Criar múltiplas posições em um batch (offline sync)"""
    try:
        results = []
        for position in bulk.positions:
            db_position = await TrackingService.create_position(
                db, technician_id, device_id, position
            )
            results.append(PositionResponse.model_validate(db_position))
        
        return {
            "message": f"{len(results)} posições salvas",
            "count": len(results),
            "positions": results,
        }
    except Exception as e:
        logger.error(f"Erro ao salvar posições em bulk: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao salvar posições",
        )


@router.get("/{technician_id}", response_model=list[PositionResponse])
async def get_technician_history(
    technician_id: str,
    hours: int = 24,
    limit: int = 1000,
    db: AsyncSession = Depends(get_db),
):
    """Obter histórico de posições de um técnico"""
    try:
        if hours < 1 or hours > 730:  # máximo 30 dias
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hours deve estar entre 1 e 730",
            )
        
        positions = await TrackingService.get_technician_positions(
            db, technician_id, hours=hours, limit=limit
        )
        return positions
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Erro ao obter histórico: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao obter histórico",
        )


@router.get("/current/all", response_model=list[dict])
async def get_all_current_positions(
    db: AsyncSession = Depends(get_db),
):
    """Obter posição atual de todos os técnicos online (para mapa em tempo real)"""
    try:
        positions = await TrackingService.get_all_technicians_current_position(db)
        return positions
    except Exception as e:
        logger.error(f"Erro ao obter posições atuais: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao obter posições",
        )


@router.get("/{technician_id}/distance", response_model=dict)
async def get_distance_traveled(
    technician_id: str,
    start_datetime: str,
    end_datetime: str,
    db: AsyncSession = Depends(get_db),
):
    """Calcular distância percorrida num período"""
    try:
        from datetime import datetime
        start = datetime.fromisoformat(start_datetime)
        end = datetime.fromisoformat(end_datetime)
        
        distance = await TrackingService.calculate_route_distance(
            db, technician_id, start, end
        )
        
        return {
            "technician_id": technician_id,
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
            "distance_km": round(distance, 2),
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de data inválido (use ISO format)",
        )
    except Exception as e:
        logger.error(f"Erro ao calcular distância: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao calcular distância",
        )