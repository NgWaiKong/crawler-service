from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class MongoDBClient:
    def __init__(self, uri: str, database: str = "crawler_service"):
        self.client: AsyncIOMotorClient = AsyncIOMotorClient(uri)
        self.db: AsyncIOMotorDatabase = self.client[database]

    async def insert(self, collection: str, doc: Dict[str, Any]) -> Optional[str]:
        try:
            result = await self.db[collection].insert_one(doc)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Insert failed: {e}")
            return None

    async def upsert(
        self, collection: str, filter_dict: Dict[str, Any], doc: Dict[str, Any]
    ) -> bool:
        try:
            await self.db[collection].update_one(
                filter_dict, {"$set": doc}, upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Upsert failed: {e}")
            return False

    def close(self):
        self.client.close()
