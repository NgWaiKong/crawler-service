from typing import Optional

from pydantic import BaseModel, Field


class MailCrawlRequest(BaseModel):
    server: str = Field(..., description="Mail server address")
    port: int = Field(..., description="Mail server port")
    username: str = Field(..., description="Email username")
    password: str = Field(..., description="Email password")
    database: str = Field(..., description="Database name")
    collection: str = Field(..., description="Collection name")
    limit: Optional[int] = Field(None, description="Limit number of emails")
    use_ssl: bool = Field(True, description="Use SSL connection")


class RssCrawlRequest(BaseModel):
    rss_url: str = Field(..., description="RSS feed URL")
    database: str = Field(..., description="Database name")
    collection: str = Field(..., description="Collection name")
    limit: Optional[int] = Field(None, description="Limit number of articles")
    fetch_full_content: bool = Field(True, description="Fetch full article content")


class CrawlResponse(BaseModel):
    success: bool
    message: str
