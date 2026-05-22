## backend/app/models/mixins.py
from sqlalchemy import Column, DateTime
from datetime import datetime


class SoftDeleteMixin:
    """Mixin para soft delete"""
    deleted_at = Column(DateTime, nullable=True, index=True)
    
    def soft_delete(self):
        """Marcar como deletado"""
        self.deleted_at = datetime.utcnow()
    
    def restore(self):
        """Restaurar registro deletado"""
        self.deleted_at = None
    
    @property
    def is_deleted(self) -> bool:
        """Verificar se está deletado"""
        return self.deleted_at is not None