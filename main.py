import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Fixed Import here!
from config.config import Config 
from database.db import init_db
from bot.commands import router as commands_router
from bot.handlers import router as handlers_router
from utils.logger import logger

async def main():
    print("🚀 Booting ANYSNAP GodAI CEO Edition...")
    
    # Init DB
    await init_db()
    
    # Setup Bot
    bot = Bot(token=Config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
    dp = Dispatcher()
    
    # Include Routers
    dp.include_router(commands_router)
    dp.include_router(handlers_router)
    
    logger.info("ANYSNAP GodAI is now LIVE and listening for CEO commands!")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Critical Bot Error: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    asyncio.run(main())