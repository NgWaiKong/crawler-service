import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from src.mail.crawler import MailCrawler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mail", tags=["mail"])


class CrawlRequest(BaseModel):
    mail_server: str = Field(..., description="Mail server address")
    mail_port: int = Field(..., description="Mail server port")
    username: str = Field(..., description="Email username")
    password: str = Field(..., description="Email password or auth code")
    database: str = Field(..., description="Database name")
    collection: str = Field(..., description="Collection name")
    limit: Optional[int] = Field(None, description="Limit number of emails")
    use_ssl: bool = Field(True, description="Use SSL connection")


class CrawlResponse(BaseModel):
    success: bool
    message: str


async def run_crawler_task(crawler: MailCrawler):
    try:
        await crawler.crawl_and_save()
    except Exception as e:
        logger.error(f"Task failed: {e}")


def build_crawler(req: CrawlRequest) -> MailCrawler:
    return MailCrawler(
        server=req.mail_server,
        port=req.mail_port,
        username=req.username,
        password=req.password,
        database=req.database,
        collection=req.collection,
        limit=req.limit,
        use_ssl=req.use_ssl,
    )


@router.post("/crawl", response_model=CrawlResponse)
async def crawl(req: CrawlRequest, background_tasks: BackgroundTasks):
    try:
        crawler = build_crawler(req)
        background_tasks.add_task(run_crawler_task, crawler)
        return CrawlResponse(success=True, message="Task accepted")
    except Exception as e:
        logger.error(f"Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
