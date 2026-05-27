from fastapi import FastAPI

from src.api import router
from src.config import APP_TITLE, LOG_LEVEL
from src.logging_setup import configure_logging

configure_logging(LOG_LEVEL)
app = FastAPI(title=APP_TITLE)
app.include_router(router)
