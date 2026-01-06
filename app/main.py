from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.bot.handlers import register_handlers
from app.bot.dispatcher import dp, bot
from aiogram.types import Update
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
register_handlers(dp)

@app.post("/webhook")
async def telegram_webhook(update: Update):
    await dp.feed_update(bot, update)
    return {"ok": True}

@app.get("/")
def root():
    return {"message": "OK"}
