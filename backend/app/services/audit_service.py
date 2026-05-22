## backend/app/services/audit_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog
import uuid
from fastapi import Request


class AuditService:
    @staticmethod
    async def log(
        db: AsyncSession,
        action: str,
        resource: str,
        resource_id: str = None,
        user_id: str = None,
        old_data: dict = None,
        new_data: dict = None,
        request: Request = None
    ):
        """Registrar ação no log de auditoria"""
        audit_log = AuditLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            old_data=old_data,
            new_data=new_data,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None
        )
        db.add(audit_log)
        await db.commit()