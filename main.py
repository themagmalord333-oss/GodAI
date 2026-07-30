import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import Config
from database.db import init_db
from bot.commands import router as commands_router
from bot.handlers import router as handlers_router
from utils.logger import logger

async def main():
    # 1. Print Startup Banner
    print("🚀 Booting MAGMA V1.0 CEO Edition...")
    
    # 2. Initialize Database & Tables
    await init_db()
    
    # 3. Setup Bot & Dispatcher
    bot = Bot(token=Config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
    dp = Dispatcher()
    
    # 4. Attach Routers (Endpoints)
    dp.include_router(commands_router)
    dp.include_router(handlers_router)
    
    # 5. Start Polling
    logger.info("MAGMA is now LIVE and listening for CEO commands on Telegram!")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Critical Bot Error: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    # Setup basic console logging for the runner
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    asyncio.run(main())