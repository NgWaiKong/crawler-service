from typing import Any, Optional

from bson import ObjectId
from pymongo import MongoClient

from src.crawlers.base import Crawler


class MongoConnection:
    def __init__(self, uri: str, database: str, collection: str, limit: Optional[int]):
        self._client = MongoClient(uri)
        self._collection = self._client[database][collection]
        self._limit = limit

    def fetch_all(self) -> list[dict[str, Any]]:
        cursor = self._collection.find({}).sort("_id", -1)
        if self._limit:
            cursor = cursor.limit(self._limit)
        return list(cursor)

    def close(self) -> None:
        self._client.close()


class MongoCrawler(Crawler):
    def __init__(
        self,
        source_uri: str,
        source_database: str,
        source_collection: str,
        target_database: str,
        target_collection: str,
        limit: Optional[int] = None,
    ):
        super().__init__(target_database, target_collection)
        self._connection = MongoConnection(
            source_uri, source_database, source_collection, limit
        )

    def crawl(self) -> list[dict]:
        try:
            docs = self._connection.fetch_all()
            self._logger.info(f"Fetched {len(docs)} documents")
            return self._ensure_ids(docs)
        except Exception as e:
            self._logger.error(f"Crawl failed: {e}")
            return []
        finally:
            self._connection.close()

    @staticmethod
    def _ensure_ids(docs: list[dict]) -> list[dict]:
        for doc in docs:
            if "_id" not in doc:
                doc["_id"] = str(ObjectId())
            elif not isinstance(doc["_id"], str):
                doc["_id"] = str(doc["_id"])
        return docs

