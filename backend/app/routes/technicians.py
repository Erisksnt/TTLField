## backend/app/routes/technicians.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.technician import Technician
from app.schemas.technician import (
    TechnicianCreate,
    TechnicianResponse,
    TechnicianLocationResponse,
    TechnicianUpdate,
)
from app.services.traccar_service import TraccarService
import logging

router = APIRouter(prefix="/technicians", tags=["technicians"])
logger = logging.getLogger(__name__)


# backend/app/routes/technicians.py

@router.post("", response_model=TechnicianResponse, status_code=status.HTTP_201_CREATED)
async def create_technician(
    technician: TechnicianCreate,
    db: AsyncSession = Depends(get_db),
):
    try:
        # Verifica se employee_id já existe no banco (não deletado)
        stmt = select(Technician).where(
            Technician.employee_id == technician.employee_id,
            Technician.deleted_at.is_(None)
        )
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de funcionário já cadastrado",
            )

        # Tenta buscar dispositivo no Traccar
        traccar_service = TraccarService()
        existing_device = await traccar_service.get_device_by_unique_id(technician.employee_id)

        if existing_device:
            device_id = str(existing_device.get("id"))
        else:
            # Cria novo dispositivo no Traccar
            new_device = await traccar_service.create_device(
                name=technician.name,
                unique_id=technician.employee_id
            )
            device_id = str(new_device.get("id")) if new_device else None

        # Prepara dados para inserção
        technician_data = technician.dict()
        technician_data["device_id"] = device_id

        db_technician = Technician(**technician_data)
        db.add(db_technician)
        await db.commit()
        await db.refresh(db_technician)

        return TechnicianResponse.model_validate(db_technician)

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Erro ao criar técnico: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao criar técnico",
        )


@router.get("", response_model=list[TechnicianLocationResponse])
async def list_technicians(
    is_online: bool = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """Listar todos os técnicos"""
    try:
        stmt = select(Technician).where(Technician.deleted_at.is_(None))
        
        if is_online is not None:
            stmt = stmt.where(Technician.is_online == is_online)
        
        stmt = stmt.offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        technicians = result.scalars().all()
        
        return [TechnicianLocationResponse.model_validate(t) for t in technicians]
    except Exception as e:
        logger.error(f"Erro ao listar técnicos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao listar técnicos",
        )


@router.get("/{technician_id}", response_model=TechnicianResponse)
async def get_technician(
    technician_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Obter detalhes de um técnico"""
    try:
        stmt = select(Technician).where(
            Technician.id == technician_id,
            Technician.deleted_at.is_(None)
        )
        result = await db.execute(stmt)
        technician = result.scalar_one_or_none()
        
        if not technician:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Técnico não encontrado",
            )
        
        return TechnicianResponse.model_validate(technician)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Erro ao obter técnico: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao obter técnico",
        )


@router.patch("/{technician_id}", response_model=TechnicianResponse)
async def update_technician(
    technician_id: str,
    technician_update: TechnicianUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Atualizar informações de um técnico"""
    try:
        stmt = select(Technician).where(
            Technician.id == technician_id,
            Technician.deleted_at.is_(None)
        )
        result = await db.execute(stmt)
        technician = result.scalar_one_or_none()
        
        if not technician:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Técnico não encontrado",
            )
        
        update_data = technician_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(technician, field, value)
        
        await db.commit()
        await db.refresh(technician)
        
        return TechnicianResponse.model_validate(technician)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Erro ao atualizar técnico: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao atualizar técnico",
        )


@router.delete("/{technician_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_technician(
    technician_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Soft delete - marcar como deletado e remover do Traccar"""
    try:
        stmt = select(Technician).where(
            Technician.id == technician_id,
            Technician.deleted_at.is_(None)
        )
        result = await db.execute(stmt)
        technician = result.scalar_one_or_none()
        
        if not technician:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Técnico não encontrado",
            )
        
        # Remover dispositivo do Traccar
        if technician.device_id:
            try:
                traccar_service = TraccarService()
                await traccar_service.delete_device(technician.device_id)
                logger.info(f"✅ Dispositivo {technician.device_id} removido do Traccar")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao remover dispositivo do Traccar: {str(e)}")
        
        # Soft delete no banco
        technician.soft_delete()
        await db.commit()
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Erro ao deletar técnico: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao deletar técnico",
        )