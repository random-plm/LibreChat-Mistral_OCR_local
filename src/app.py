from fastapi import FastAPI

from src.api import router
from src.config import APP_TITLE

app = FastAPI(title=APP_TITLE)
app.include_router(router)
