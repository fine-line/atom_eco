from fastapi import FastAPI
from contextlib import asynccontextmanager
from .routers import companies, storages, system
from .database import create_db_and_tables


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

app.include_router(router=companies.router, prefix="/v1")
app.include_router(router=storages.router, prefix="/v1")
app.include_router(router=system.router, prefix="/v1")


@app.get("/")
async def root():
    return {"version": "1"}
