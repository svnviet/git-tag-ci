from contextlib import asynccontextmanager

from fastapi import FastAPI

from . import worker
from .db import init_db
from .routers import downloads, pages, tags


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    worker.start()
    yield
    worker.stop()


app = FastAPI(title="git-tag-ci", lifespan=lifespan)

# downloads first: /tags/{name:path}/download/... must match before the catch-all /tags/{name:path}
app.include_router(downloads.router)
app.include_router(tags.router)
app.include_router(pages.router)
