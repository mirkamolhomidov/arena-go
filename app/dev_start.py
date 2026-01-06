import asyncio
from app.bot.dispatcher import bot, dp
from app.bot.handlers import register_handlers

async def main():
    register_handlers(dp)
    
    print("Bot pollingda ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())