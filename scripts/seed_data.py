import asyncio
import json
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.db import AsyncSessionLocal, init_db, UserDB


async def seed():
    print("[Seed] Initializing database...")
    await init_db()

    async with AsyncSessionLocal() as session:
        # Seed default user
        user = UserDB(
            id="user_123",
            username="alex_traveler",
            email="alex@traveler.com",
            full_name="Alex Mercer",
            phone_number="+91-9876543210",
            preferences_json=json.dumps({
                "preferred_hotel_stars": 5,
                "max_hotel_budget_per_night": 15000.0,
                "preferred_ride_type": "Sedan",
                "preferred_amenities": ["Free WiFi", "Swimming Pool", "Spa"],
                "home_city": "Bengaluru"
            })
        )
        session.add(user)
        try:
            await session.commit()
            print("[Seed] Successfully seeded initial demo user 'user_123'.")
        except Exception as e:
            await session.rollback()
            print(f"[Seed] User already exists or error: {e}")

    print("[Seed] Database seeding completed.")


if __name__ == "__main__":
    asyncio.run(seed())
