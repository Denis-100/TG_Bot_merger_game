# scripts/migrate_to_postgres.py
import asyncio
import aiosqlite
import asyncpg
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))


async def migrate_sqlite_to_postgres():
    """Переносит данные из SQLite в PostgreSQL на Railway"""

    print("🔄 Начинаем миграцию из SQLite в PostgreSQL...")

    # Локальный SQLite
    sqlite_db = "users.db"
    if not os.path.exists(sqlite_db):
        print(f"❌ Файл {sqlite_db} не найден")
        return

    # PostgreSQL на Railway
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL не установлен")
        print("💡 Получите в Railway: Database → Connect → Postgres Connection URL")
        return

    # Конвертируем URL если нужно
    if database_url.startswith("postgresql://"):
        # Оставляем как есть
        pass
    elif database_url.startswith("postgres://"):
        # Конвертируем для asyncpg
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    print(f"📊 SQLite: {sqlite_db}")
    print(f"🔗 PostgreSQL URL: {database_url[:50]}...")

    # Подключаемся к SQLite
    sqlite_conn = await aiosqlite.connect(sqlite_db)

    try:
        # Подключаемся к PostgreSQL
        pg_conn = await asyncpg.connect(database_url)
        print("✅ Подключение к PostgreSQL установлено")

        # Создаем таблицы в PostgreSQL
        await pg_conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                money DOUBLE PRECISION DEFAULT 0,
                bronze_coin_bought INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        await pg_conn.execute('''
            CREATE TABLE IF NOT EXISTS user_coins (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                coin_type TEXT NOT NULL,
                count INTEGER DEFAULT 0,
                UNIQUE(user_id, coin_type)
            )
        ''')

        # Мигрируем пользователей
        sqlite_cursor = await sqlite_conn.execute('SELECT * FROM users')
        users = await sqlite_cursor.fetchall()

        migrated = 0
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
            migrated += 1

        print(f"✅ Пользователей мигрировано: {migrated}")

        # Мигрируем монеты
        sqlite_cursor = await sqlite_conn.execute('SELECT * FROM user_coins')
        coins = await sqlite_cursor.fetchall()

        coin_migrated = 0
        for coin in coins:
            await pg_conn.execute('''
                INSERT INTO user_coins (user_id, coin_type, count)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id, coin_type) DO UPDATE SET
                    count = EXCLUDED.count
            ''', coin[1], coin[2], coin[3])
            coin_migrated += 1

        print(f"✅ Монет мигрировано: {coin_migrated}")

        # Статистика
        total_users = await pg_conn.fetchval('SELECT COUNT(*) FROM users')
        total_money = await pg_conn.fetchval('SELECT SUM(money) FROM users') or 0

        print(f"\n📊 В PostgreSQL теперь:")
        print(f"   👥 Пользователей: {total_users}")
        print(f"   💰 Общий баланс: {total_money:,.0f}")

        await pg_conn.close()

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await sqlite_conn.close()

    print("\n🎯 Миграция завершена!")


if __name__ == "__main__":
    asyncio.run(migrate_sqlite_to_postgres())