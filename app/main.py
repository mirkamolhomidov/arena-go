from fastapi import FastAPI
from app.database import create_db_and_tables
from app.routers import districts

app = FastAPI(
    title="Stadium bot API",
    version="1.0.0"
)

app.include_router(districts.router)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
def root():
    return {"message": "OK"}
