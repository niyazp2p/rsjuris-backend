import asyncio
from sqlalchemy.future import select
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.models.enums import Role
from app.core.security import get_password_hash

async def seed_super_admin():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == "admin@rsjuris.com"))
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            print("Super Admin already exists: admin@rsjuris.com")
            return

        admin = User(
            email="admin@rsjuris.com",
            password_hash=get_password_hash("Admin@RSJuris2026"),
            full_name="Managing Partner",
            designation="Managing Counsel & Partner",
            role=Role.SUPER_ADMIN,
            is_active=True
        )
        db.add(admin)
        await db.commit()
        print("✓ Initial Super Admin seeded: admin@rsjuris.com / Admin@RSJuris2026")

if __name__ == "__main__":
    asyncio.run(seed_super_admin())