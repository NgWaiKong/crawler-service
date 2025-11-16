from datetime import datetime
from typing import Any

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
    def __init__(self, urls: list[str], database: str, collection: str):
        super().__init__(database, collection)
        self._urls = urls
        self._http = HttpClient(user_agent="Mozilla/5.0 (compatible; RSS Reader/1.0)")
        self._parser = FeedParser()

    def crawl(self) -> list[dict]:
        try:
            articles = [
                article
                for url in self._urls
                for article in self._crawl_feed(url)
            ]
            return articles
        finally:
            self._http.close()

    def _crawl_feed(self, url: str) -> list[dict]:
        try:
            content = self._http.get(url)
            articles = self._parser.parse(content, url)
            self._logger.info(f"Crawled {len(articles)} articles from {url}")
            return [article.to_dict() for article in articles]
        except Exception as e:
            self._logger.warning(f"Failed to crawl {url}: {type(e).__name__}")
            return []
