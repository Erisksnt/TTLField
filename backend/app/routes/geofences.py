## backend/app/routes/geofences.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.geofence import Geofence
from app.schemas.geofence import GeofenceCreate, GeofenceResponse, GeofenceUpdate
from app.models.user import User
from app.utils.dependencies import get_current_user, require_roles
import logging

router = APIRouter(prefix="/geofences", tags=["geofences"])
logger = logging.getLogger(__name__)


@router.post("", response_model=GeofenceResponse, status_code=status.HTTP_201_CREATED)
async def create_geofence(
    geofence: GeofenceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "manager", "supervisor")),
):
    """Criar novo geofence"""
    try:
        # Verifique se os dados estão chegando
        logger.info(f"Dados recebidos: center_latitude={geofence.center_latitude}, center_longitude={geofence.center_longitude}, radius={geofence.radius}")
        
        db_geofence = Geofence(**geofence.dict())
        db.add(db_geofence)
        await db.commit()
        await db.refresh(db_geofence)
        return GeofenceResponse.model_validate(db_geofence)
    except Exception as e:
        logger.error(f"Erro ao criar geofence: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao criar geofence",
        )


@router.get("", response_model=list[GeofenceResponse])
async def list_geofences(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Listar todos os geofences"""
    try:
        stmt = select(Geofence).where(Geofence.deleted_at.is_(None))
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        geofences = result.scalars().all()
        return [GeofenceResponse.model_validate(g) for g in geofences]
    except Exception as e:
        logger.error(f"Erro ao listar geofences: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao listar geofences",
        )


@router.get("/{geofence_id}", response_model=GeofenceResponse)
async def get_geofence(
    geofence_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Obter detalhes de um geofence"""
    try:
        stmt = select(Geofence).where(
            Geofence.id == geofence_id,
            Geofence.deleted_at.is_(None)
        )
        result = await db.execute(stmt)
        geofence = result.scalar_one_or_none()
        if not geofence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Geofence não encontrado",
            )
        return GeofenceResponse.model_validate(geofence)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Erro ao obter geofence: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao obter geofence",
        )


@router.patch("/{geofence_id}", response_model=GeofenceResponse)
async def update_geofence(
    geofence_id: str,
    geofence_update: GeofenceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "manager", "supervisor")),
):
    """Atualizar geofence"""
    try:
        stmt = select(Geofence).where(
            Geofence.id == geofence_id,
            Geofence.deleted_at.is_(None)
        )
        result = await db.execute(stmt)
        geofence = result.scalar_one_or_none()
        if not geofence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Geofence não encontrado",
            )
        
        update_data = geofence_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(geofence, field, value)
        
        await db.commit()
        await db.refresh(geofence)
        return GeofenceResponse.model_validate(geofence)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Erro ao atualizar geofence: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao atualizar geofence",
        )


@router.delete("/{geofence_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_geofence(
    geofence_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "manager")),
):
    """Soft delete - marcar como deletado"""
    try:
        stmt = select(Geofence).where(
            Geofence.id == geofence_id,
            Geofence.deleted_at.is_(None)
        )
        result = await db.execute(stmt)
        geofence = result.scalar_one_or_none()
        if not geofence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Geofence não encontrado",
            )
        
        geofence.soft_delete()
        await db.commit()
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Erro ao deletar geofence: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao deletar geofence",
        )