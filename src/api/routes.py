from fastapi import APIRouter, BackgroundTasks

from src.api.schemas import MailCrawlRequest, RssCrawlRequest, CrawlResponse
from src.config.settings import get_settings
from src.crawlers.mail import MailCrawler
from src.crawlers.rss import RssCrawler
from src.infrastructure.database import Database


router = APIRouter()


async def _execute_crawler(crawler, mongo_uri: str, database: str):
    db = Database(mongo_uri, database)
    try:
        await crawler.execute(db)
    finally:
        db.close()


@router.post("/mail/crawl", response_model=CrawlResponse, tags=["mail"])
async def crawl_mail(req: MailCrawlRequest, tasks: BackgroundTasks):
    settings = get_settings()
    crawler = MailCrawler(
        server=req.server,
        port=req.port,
        username=req.username,
        password=req.password,
        database=req.database,
        collection=req.collection,
        limit=req.limit,
        use_ssl=req.use_ssl,
    )
    tasks.add_task(_execute_crawler, crawler, settings.mongo_uri, req.database)
    return CrawlResponse(success=True, message="Task accepted")


@router.post("/rss/crawl", response_model=CrawlResponse, tags=["rss"])
async def crawl_rss(req: RssCrawlRequest, tasks: BackgroundTasks):
    settings = get_settings()
    crawler = RssCrawler(urls=req.urls, database=req.database, collection=req.collection)
    tasks.add_task(_execute_crawler, crawler, settings.mongo_uri, req.database)
    return CrawlResponse(success=True, message="Task accepted")
