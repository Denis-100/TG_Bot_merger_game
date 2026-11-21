# start_bot.py
import os
import sys
import asyncio


def check_environment():
    """Проверка окружения для Railway"""
    print("🔍 Проверка окружения Railway...")

    # На Railway переменные окружения устанавливаются автоматически
    # Проверяем только наличие BOT_TOKEN
    
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        print("❌ BOT_TOKEN не найден в переменных окружения!")
        print("   Установите в Railway: Settings → Variables")
        print("   Key: BOT_TOKEN, Value: ваш_токен_бота")
        return False
    
    print(f"✅ BOT_TOKEN: {bot_token[:10]}...")
    
    # Проверяем DATABASE_URL
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        if 'postgresql://' in db_url:
            print("✅ Используется PostgreSQL (Railway)")
        else:
            print(f"✅ DATABASE_URL: {db_url[:50]}...")
    else:
        print("ℹ️  DATABASE_URL не установлен, используется SQLite")
    
    return True


async def main():
    """Основная функция"""
    print("🤖 ЗАПУСК БОТА MergeToGetRich")
    print("=" * 50)

    # 1. Проверяем окружение
    if not check_environment():
        print("\n❌ Проблемы с окружением")
        return

    # 2. Запускаем основной модуль бота
    print("\n" + "=" * 50)
    print("🚀 ЗАПУСК ОСНОВНОГО БОТА")
    print("=" * 50)

    try:
        # Импортируем и запускаем основной модуль
        from main import main as bot_main
        await bot_main()
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка запуска: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Настройка для Windows (если локально)
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    # Запускаем
    asyncio.run(main())
