from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime, timezone
import logging

from src.core.config import settings
from src.core.mongodb import MongoDBClient

logger = logging.getLogger(__name__)


class BaseCrawler(ABC):
    @property
    @abstractmethod
    def database_name(self) -> str:
        pass

    @property
    @abstractmethod
    def collection_name(self) -> str:
        pass

    @abstractmethod
    def crawl(self, **kwargs) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_document_id(self, item: Dict[str, Any]) -> str:
        pass

    async def save_items(self, items: List[Dict[str, Any]], mongo: MongoDBClient):
        for item in items:
            item["created_at"] = (
                datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            )
            doc_id = self.get_document_id(item)
            await mongo.upsert(self.collection_name, {"_id": doc_id}, item)

    async def crawl_and_save(self, **kwargs) -> Dict[str, Any]:
        items = self.crawl(**kwargs)
        if not items:
            return {"success": True, "message": "No data", "total": 0}
        mongo = MongoDBClient(settings.mongo_uri, self.database_name)
        try:
            await self.save_items(items, mongo)
            return {"success": True, "message": "Completed", "total": len(items)}
        except Exception as e:
            logger.error(f"Save failed: {e}")
            return {"success": False, "message": str(e), "total": 0}
        finally:
            mongo.close()
