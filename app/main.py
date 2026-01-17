from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import create_db_and_tables
from app.routers.routers import Routes

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(
    title="Stadium bot API",
    version="1.0.0",
    lifespan=lifespan
)

Routes('/api', app)

@app.get("/")
def root():
    return {"message": "OK"}
