# scripts/auto_migrate.py
import asyncio
import aiosqlite
import asyncpg
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))


async def migrate_if_needed():
    """Проверяет и выполняет миграцию из SQLite в PostgreSQL при необходимости"""

    print("🔍 Проверка необходимости миграции...")

    # Проверяем, что мы в продакшене с PostgreSQL
    # if os.getenv("ENVIRONMENT") != "production":
    #     print("ℹ️  Не продакшн, миграция не требуется")
    #     return False

    # Проверяем существование SQLite файла
    sqlite_db = "users.db"
    if not os.path.exists(sqlite_db):
        print("ℹ️  Файл users.db не найден, пропускаем миграцию")
        return False

    # Получаем строку подключения PostgreSQL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL не установлен")
        return False

    # Конвертируем URL если нужно
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    print(f"📦 Начинаем миграцию из {sqlite_db} в PostgreSQL...")

    try:
        # Подключаемся к обеим базам
        sqlite_conn = await aiosqlite.connect(sqlite_db)
        pg_conn = await asyncpg.connect(database_url)

        # 1. Проверяем, есть ли уже данные в PostgreSQL
        pg_users_count = await pg_conn.fetchval('SELECT COUNT(*) FROM users')

        # Если в PostgreSQL уже есть данные, спрашиваем подтверждение
        if pg_users_count > 0:
            print(f"⚠️  В PostgreSQL уже есть {pg_users_count} пользователей")

            # На Railway нет интерактивного ввода, используем переменную окружения
            force_migrate = os.getenv("FORCE_MIGRATE", "false").lower() == "true"

            if not force_migrate:
                print("ℹ️  Пропускаем миграцию (установите FORCE_MIGRATE=true для принудительной)")
                await pg_conn.close()
                await sqlite_conn.close()
                return False

        # 2. Мигрируем пользователей
        sqlite_cursor = await sqlite_conn.execute('SELECT * FROM users')
        users = await sqlite_cursor.fetchall()

        migrated_users = 0
        for user in users:
            await pg_conn.execute('''
                INSERT INTO users (user_id, username, first_name, money, bronze_coin_bought)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (user_id) DO UPDATE SET
                    username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name,
                    money = EXCLUDED.money,
                    bronze_coin_bought = EXCLUDED.bronze_coin_bought
            ''', user[0], user[1], user[2], user[3], user[4])
            migrated_users += 1

        # 3. Мигрируем монеты
        sqlite_cursor = await sqlite_conn.execute('SELECT * FROM user_coins')
        coins = await sqlite_cursor.fetchall()

        migrated_coins = 0
        for coin in coins:
            await pg_conn.execute('''
                INSERT INTO user_coins (user_id, coin_type, count)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id, coin_type) DO UPDATE SET
                    count = EXCLUDED.count
            ''', coin[1], coin[2], coin[3])
            migrated_coins += 1

        # 4. Статистика
        total_users = await pg_conn.fetchval('SELECT COUNT(*) FROM users')
        total_money = await pg_conn.fetchval('SELECT SUM(money) FROM users') or 0

        print(f"\n✅ Миграция завершена успешно!")
        print(f"   👥 Пользователей перенесено: {migrated_users}")
        print(f"   🟤 Записей монет: {migrated_coins}")
        print(f"   📊 Всего в PostgreSQL: {total_users} пользователей")
        print(f"   💰 Общий баланс: {total_money:,.0f}")

        # 5. Создаем резервную копию SQLite
        import shutil
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f'/tmp/users_backup_{timestamp}.db'
        shutil.copy2(sqlite_db, backup_path)
        print(f"   💾 Резервная копия: {backup_path}")

        # 6. Опционально: удаляем SQLite файл после миграции
        if os.getenv("REMOVE_SQLITE_AFTER_MIGRATE", "false").lower() == "true":
            os.remove(sqlite_db)
            print("   🗑️  Файл users.db удален после миграции")

        await pg_conn.close()
        await sqlite_conn.close()

        return True

    except Exception as e:
        print(f"❌ Ошибка при миграции: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(migrate_if_needed())
    sys.exit(0 if success else 1)