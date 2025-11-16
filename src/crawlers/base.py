from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from src.infrastructure.database import Database
from src.infrastructure.logger import setup_logger


class Crawler(ABC):
    def __init__(self, database: str, collection: str):
        self._database = database
        self._collection = collection
        self._logger = setup_logger(self.__class__.__name__)

    @property
    def database(self) -> str:
        return self._database

    @property
    def collection(self) -> str:
        return self._collection

    @abstractmethod
    def crawl(self) -> list[dict[str, Any]]:
        pass

    async def execute(self, db: Database) -> dict[str, Any]:
        items = self.crawl()
        
        if not items:
            self._logger.warning("No data fetched")
            return {"success": True, "message": "No data", "total": 0}
        
        self._logger.info(f"Fetched {len(items)} items")
        await self._save(items, db)
        self._logger.info(f"Saved {len(items)} items")
        return {"success": True, "message": "Completed", "total": len(items)}

    async def _save(self, items: list[dict[str, Any]], db: Database) -> None:
        for item in items:
            item["created_at"] = self._now()
            await db.upsert(self._collection, {"_id": item["_id"]}, item)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
