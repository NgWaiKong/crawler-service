from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from src.infrastructure.logger import setup_logger


logger = setup_logger(__name__)


class Database:
    def __init__(self, uri: str, database: str):
        self._client = AsyncIOMotorClient(uri)
        self._db: AsyncIOMotorDatabase = self._client[database]

    @property
    def db(self) -> AsyncIOMotorDatabase:
        return self._db

    async def upsert(
        self, collection: str, filter_doc: dict[str, Any], doc: dict[str, Any]
    ) -> None:
        try:
            await self._db[collection].update_one(
                filter_doc, {"$set": doc}, upsert=True
            )
        except Exception as e:
            logger.error(f"Upsert failed: {collection}, id={filter_doc.get('_id')}, error={e}")
            raise

    def close(self) -> None:
        self._client.close()
