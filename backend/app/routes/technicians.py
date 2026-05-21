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
import logging

router = APIRouter(prefix="/technicians", tags=["technicians"])
logger = logging.getLogger(__name__)


@router.post("", response_model=TechnicianResponse, status_code=status.HTTP_201_CREATED)
async def create_technician(
    technician: TechnicianCreate,
    db: AsyncSession = Depends(get_db),
):
    """Criar novo técnico"""
    try:
        # Verificar se employee_id já existe
        stmt = select(Technician).where(Technician.employee_id == technician.employee_id)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de funcionário já cadastrado",
            )
        
        db_technician = Technician(**technician.dict())
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
        stmt = select(Technician)
        
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
        stmt = select(Technician).where(Technician.id == technician_id)
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
        stmt = select(Technician).where(Technician.id == technician_id)
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
    """Deletar um técnico"""
    try:
        stmt = select(Technician).where(Technician.id == technician_id)
        result = await db.execute(stmt)
        technician = result.scalar_one_or_none()
        
        if not technician:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Técnico não encontrado",
            )
        
        await db.delete(technician)
        await db.commit()
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Erro ao deletar técnico: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao deletar técnico",
        )
