import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router
from src.config.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    _configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_title,
        version=settings.app_version,
        description="Crawler service for collecting information",
    )

    _add_middleware(app)
    _add_routes(app)

    return app


def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def _add_middleware(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def _add_routes(app: FastAPI) -> None:
    app.include_router(router, prefix="/api/v1")

    @app.get("/")
    async def root():
        settings = get_settings()
        return {
            "service": settings.app_title,
            "version": settings.app_version,
            "status": "running",
        }


app = create_app()
