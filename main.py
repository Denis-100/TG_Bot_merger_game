# main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN, DB_TYPE
from handlers.main_handlers import router
from database import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Основная асинхронная функция запуска бота"""
    print(f"🤖 Запуск бота. Тип БД: {DB_TYPE}")

    try:
        # Подключаемся к базе данных
        await db.connect()
        print("✅ База данных подключена")
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к БД: {e}")
        print("❌ Не удалось подключиться к базе данных")
        print("   Проверьте настройки в .env.local")
        return

    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Регистрируем роутер
    dp.include_router(router)

    # Запускаем фоновую задачу для дохода
    try:
        from database.income_service import income_loop
        income_task = asyncio.create_task(income_loop())
        print("✅ Фоновая задача дохода запущена")
    except Exception as e:
        logger.error(f"❌ Ошибка запуска income_loop: {e}")
        income_task = None

    try:
        logger.info("Бот запущен")
        print("✅ Бот запущен и готов к работе!")
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
        print("\n🛑 Бот остановлен")
    finally:
        if income_task:
            income_task.cancel()
        await bot.session.close()
        await db.close()
        print("👋 Соединения закрыты")



if __name__ == "__main__":
    asyncio.run(main())
