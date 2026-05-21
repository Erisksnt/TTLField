## backend/app/models/token_blacklist.py
from sqlalchemy import Column, String, DateTime
from app.database import Base
from datetime import datetime


class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"

    token = Column(String(500), primary_key=True, index=True)
    revoked_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

    def __repr__(self):
        return f"<TokenBlacklist token={self.token[:20]}...>"