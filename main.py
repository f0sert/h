import asyncio
import logging
from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from handlers.common import router as common_router
from handlers.deffer import router as deffer_router
from handlers.admin import router as admin_router

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.ERROR
)

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(admin_router)
    dp.include_router(deffer_router)
    dp.include_router(common_router)

    print("Бот запущен! Made with 💖 by @fos3rt, special for Sally`s defence team 😁")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())