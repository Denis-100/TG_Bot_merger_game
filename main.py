import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from database.async_db import income_loop
from handlers.main_handlers import router  # Импортируем один роутер

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_data_integrity():
    """Проверяет целостность данных при запуске"""
    from database.async_db import read_users_file, create_backup

    try:
        data = await read_users_file()
        if data:
            print(f"✅ Данные загружены. Пользователей: {len(data)}")

            # Создаем резервную копию
            backup = await create_backup()
            if backup:
                print(f"✅ Создана резервная копия: {backup}")
    except Exception as e:
        print(f"❌ Ошибка при проверке данных: {e}")


async def main():
    """Основная асинхронная функция запуска бота"""
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Регистрируем один роутер
    dp.include_router(router)

    # Запускаем фоновую задачу для дохода
    income_task = asyncio.create_task(income_loop())

    try:
        logger.info("Бот запущен")
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    finally:
        income_task.cancel()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())