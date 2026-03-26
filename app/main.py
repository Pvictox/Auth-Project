from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import Database
from app.log_config.logging_config import get_logger, setup_logging
from app.routers import routers

from .redis_config import RedisConfig
from .seeds import check_and_seed

setup_logging()
logger = get_logger(__name__)


def router_includer(app: FastAPI) -> None:
    """
    Include all routers in the FastAPI application.
    """
    for router in routers:
        app.include_router(router.router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if app.state.database.check_connection():
        check_and_seed()
        logger.info("Starting up application...")

    if RedisConfig.check_connection():
        logger.info("Redis connection is healthy.")
    yield
    RedisConfig.close()
    logger.info("Shutting down application...")


def create_app() -> FastAPI:
    app = FastAPI(title="Auth Project", version="1.0.0", lifespan=lifespan)
    app.state.database = Database()

    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include all routers
    router_includer(app)
    logger.info("Application created successfully")
    return app


app = create_app()


@app.middleware("http")
async def log_requests(request, call_next):
    logger.info("Incoming request: %s %s", request.method, request.url)
    response = await call_next(request)
    logger.info(
        "Response status: %d for %s %s",
        response.status_code,
        request.method,
        request.url,
    )
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(
        "Unhandled exception: %s for request %s %s",
        exc,
        request.method,
        request.url,
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred. Please try again later."
        },
    )
