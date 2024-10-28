import asyncio
from aiogram import Bot, Dispatcher

from app.handlers import router
from app.database.models import async_main
from dotenv import load_dotenv
import os

load_dotenv()

api_token = os.getenv('API_TOKEN')

bot = Bot(token=api_token)


async def main():
    await async_main()
    bot = Bot(token=api_token)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())