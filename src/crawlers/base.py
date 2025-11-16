from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from src.infrastructure.database import Database


class Crawler(ABC):
    def __init__(self, database: str, collection: str):
        self._database = database
        self._collection = collection

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
            return {"success": True, "message": "No data", "total": 0}
        await self._save(items, db)
        return {"success": True, "message": "Completed", "total": len(items)}

    async def _save(self, items: list[dict[str, Any]], db: Database) -> None:
        for item in items:
            item["created_at"] = self._now()
            await db.upsert(self._collection, {"_id": item["_id"]}, item)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
