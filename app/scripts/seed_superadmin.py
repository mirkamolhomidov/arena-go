import os
import json
import asyncio
from dotenv import load_dotenv
from sqlalchemy.dialects.postgresql import insert

from app.database import async_session_factory
from app.models.users import Users

load_dotenv(".env.seed")

async def seed_superadmins():
    """Seed initial superadmin users through the async database session."""
    raw = os.getenv("SUPERADMINS")
    if not raw:
        print("Skipping seeding")
        return

    admins = json.loads(raw)

    async with async_session_factory() as db:
        stmt = insert(Users).values(admins)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["telegram_id"]
        )

        await db.execute(stmt)
        await db.commit()

if __name__ == "__main__":
    asyncio.run(seed_superadmins())
    print("Superadmins seeded successfully")
