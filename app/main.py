from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from .routers import companies, login, storages, locations, admin, wastes
from .database import create_db_and_tables
from .config import Settings, get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup
    create_db_and_tables()
    yield
    # On shutdown

app = FastAPI(
    root_path="/api", lifespan=lifespan, title="Atom ECO",
    summary="Cleanliness is not where there is no littering, but where there \
        is cleaning")

app.include_router(router=login.router, prefix="/v1")
app.include_router(router=wastes.router, prefix="/v1")
app.include_router(router=companies.router, prefix="/v1")
app.include_router(router=storages.router, prefix="/v1")
app.include_router(router=locations.router, prefix="/v1")
app.include_router(router=admin.router, prefix="/v1")


@app.get("/")
async def info(settings: Settings = Depends(get_settings)):
    return {
            "version": settings.version,
            "docs url": settings.docs_url
            }
