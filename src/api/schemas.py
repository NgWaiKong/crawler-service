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
    urls: list[str] = Field(..., description="RSS feed URLs")
    database: str = Field(..., description="Database name")
    collection: str = Field(..., description="Collection name")


class MongoCrawlRequest(BaseModel):
    source_uri: str = Field(..., description="Source MongoDB URI")
    source_database: str = Field(..., description="Source database name")
    source_collection: str = Field(..., description="Source collection name")
    target_database: str = Field(..., description="Target database name")
    target_collection: str = Field(..., description="Target collection name")
    limit: Optional[int] = Field(None, description="Limit number of documents")


class CrawlResponse(BaseModel):
    success: bool
    message: str
