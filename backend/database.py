"""Database connection and configuration"""
import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME", "haven_therapy")

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

async def close_db():
    """Close database connection"""
    client.close()
