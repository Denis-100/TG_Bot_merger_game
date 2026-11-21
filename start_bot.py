# start_bot.py
# !/usr/bin/env python3
"""
Упрощенный запуск бота с исправлениями
"""
import os
import sys
import asyncio


def check_environment():
    """Проверка окружения"""
    print("🔍 Проверка окружения...")

    # Проверяем .env.local
    if not os.path.exists('.env.local'):
        print("❌ .env.local не найден!")
        return False
    else:
        with open('.env.local', 'r') as f:
        content = f.read()
        
    if not os.path.exists('.env'):
        print("❌ .env не найден!")
        return False
    else:
        with open('.env', 'r') as f:
            content = f.read()

    if 'BOT_TOKEN=' not in content:
        print("❌ BOT_TOKEN не найден в .env.local")
        return False

    if 'ENVIRONMENT=development' not in content:
        print("⚠️  ENVIRONMENT не установлен в development")

    print("✅ Окружение проверено")
    return True


def fix_database_import():
    """Исправление импорта базы данных"""
    print("\n🔧 Проверка конфигурации БД...")

    # Загружаем конфигурацию вручную
    from dotenv import load_dotenv
    load_dotenv('.env.local')

    # Определяем тип БД
    db_url = os.getenv("DATABASE_URL", "sqlite:///users.db")

    if db_url.startswith('postgresql://'):
        db_type = 'postgresql'
        print(f"  🚀 Тип БД: PostgreSQL")
    elif db_url.startswith('sqlite:///'):
        db_type = 'sqlite'
        print(f"  🔧 Тип БД: SQLite")
    else:
        db_type = 'sqlite'
        print(f"  🔧 Тип БД: SQLite (по умолчанию)")

    return db_type


async def test_database_connection(db_type):
    """Тестирование подключения к БД"""
    print(f"\n🧪 Тест подключения к БД ({db_type})...")

    try:
        if db_type == 'sqlite':
            from database.sqlite_manager import SQLiteDatabase

            # Создаем экземпляр SQLite
            db = SQLiteDatabase("users.db")
            await db.connect()

            # Тестируем
            user = await db.get_or_create_user(999999, "test_bot")
            print(f"  ✅ SQLite работает. Пользователь: {user['username']}")

            await db.close()
            return True

        else:  # PostgreSQL
            from database.db_manager import db

            await db.connect()
            print("  ✅ PostgreSQL подключена")

            await db.close()
            return True

    except Exception as e:
        print(f"  ❌ Ошибка подключения: {e}")
        return False


async def run_bot():
    """Запуск бота"""
    print("\n" + "=" * 50)
    print("🚀 ЗАПУСК БОТА")
    print("=" * 50)

    try:
        # Импортируем и запускаем основной модуль
        from main import main
        await main()
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка запуска: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Основная функция"""
    print("🤖 ЗАПУСК БОТА MergeToGetRich")
    print("=" * 50)

    # 1. Проверяем окружение
    if not check_environment():
        print("\n❌ Проблемы с окружением")
        return

    # 2. Загружаем переменные
    from dotenv import load_dotenv
    load_dotenv('.env.local', override=True)
    print("✅ Переменные окружения загружены")

    # 3. Проверяем токен
    token = os.environ.get('BOT_TOKEN')
    if not token or ':' not in token:
        print("❌ Неверный токен бота!")
        return

    print(f"🤖 Токен: {token[:10]}...")

    # 4. Определяем тип БД
    db_type = fix_database_import()

    # 5. Тестируем подключение к БД
    if not await test_database_connection(db_type):
        print("\n⚠️  Проблемы с базой данных, но пробуем запустить...")

    # 6. Запускаем бота
    await run_bot()


if __name__ == "__main__":
    # Настройка для Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    # Запускаем
    asyncio.run(main())
