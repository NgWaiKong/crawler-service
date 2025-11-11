import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.mail.api import router as mail_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(
    title="Crawler Service",
    version="0.1.0",
    description="Crawler service for collecting information",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mail_router)


@app.get("/")
async def root():
    return {"service": "Crawler Service", "version": "0.1.0", "status": "running"}
