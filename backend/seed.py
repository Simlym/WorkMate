"""Initialize test users. Run once: uv run python seed.py"""
import asyncio
from app.database import AsyncSessionLocal, init_db
from app.models.user import User
from app.core.security import hash_password


async def main():
    await init_db()
    async with AsyncSessionLocal() as db:
        users = [
            User(employee_id="admin", password_hash=hash_password("admin123"), display_name="管理员"),
            User(employee_id="test001", password_hash=hash_password("test123"), display_name="测试用户"),
        ]
        for u in users:
            db.add(u)
        await db.commit()
        print("Seed completed: admin/admin123, test001/test123")


asyncio.run(main())
