from datetime import datetime
from typing import Optional, Any

import feedparser

from src.crawlers.base import Crawler
from src.domain.models import RssArticle
from src.infrastructure.http import HttpClient


class FeedParser:
    def parse(self, content: str, feed_url: str) -> list[RssArticle]:
        feed = feedparser.parse(content)
        return [self._create_article(entry, feed_url) for entry in feed.entries]

    def _create_article(self, entry: Any, feed_url: str) -> RssArticle:
        return RssArticle(
            title=entry.get("title", ""),
            link=entry.get("link", ""),
            published=self._parse_time(entry),
            summary=entry.get("summary", ""),
            content=self._extract_content(entry),
            author=entry.get("author", ""),
            feed_title="",
            feed_url=feed_url,
        )

    @staticmethod
    def _parse_time(entry: Any) -> str:
        time_tuple = entry.get("published_parsed") or entry.get("updated_parsed")
        return datetime(*time_tuple[:6]).isoformat() if time_tuple else ""

    @staticmethod
    def _extract_content(entry: Any) -> str:
        if content := entry.get("content"):
            return content[0].get("value", "")
        return entry.get("description", "")


class RssCrawler(Crawler):
    def __init__(
        self,
        rss_url: str,
        database: str,
        collection: str,
        limit: Optional[int] = None,
        fetch_full_content: bool = True,
    ):
        super().__init__(database, collection)
        self._rss_url = rss_url
        self._limit = limit
        self._fetch_full = fetch_full_content
        self._http = HttpClient(user_agent="Mozilla/5.0 (compatible; RSS Reader/1.0)")
        self._parser = FeedParser()

    def crawl(self) -> list[dict]:
        try:
            content = self._http.get(self._rss_url)
            articles = self._parser.parse(content, self._rss_url)
            items = [article.to_dict() for article in articles]
            if self._fetch_full:
                self._enrich(items)
            return items[: self._limit] if self._limit else items
        except Exception:
            return []
        finally:
            self._http.close()

    def _enrich(self, items: list[dict]) -> None:
        for item in items:
            if link := item.get("link"):
                try:
                    item["content"] = self._http.get(link)
                except Exception:
                    pass

