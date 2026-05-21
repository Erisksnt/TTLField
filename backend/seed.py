import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.models import User
from app.utils.security import hash_password
from app.config import get_settings
import uuid

settings = get_settings()

async def seed_admin_user():
    engine = create_async_engine(
        settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
        echo=False,
    )
    
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        from sqlalchemy.future import select
        stmt = select(User).where(User.email == "admin@example.com")
        result = await session.execute(stmt)
        admin = result.scalar_one_or_none()
        
        if admin:
            print("✅ Admin user já existe!")
            return
        
        admin_user = User(
            id=str(uuid.uuid4()),
            email="admin@example.com",
            username="admin",
            hashed_password=hash_password("password123"),
            full_name="Administrator",
            role="admin",
            is_active=True,
            is_admin=True,
        )
        
        session.add(admin_user)
        await session.commit()
        
        print("✅ Admin user created successfully!")

if __name__ == "__main__":
    asyncio.run(seed_admin_user())