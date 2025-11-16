from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase


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
        await self._db[collection].update_one(filter_doc, {"$set": doc}, upsert=True)

    def close(self) -> None:
        self._client.close()
