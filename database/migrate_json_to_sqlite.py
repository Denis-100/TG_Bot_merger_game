import json
import asyncio
import aiosqlite
import sys
import os

# ============================================
# ВАЖНО: Импортируем через относительный путь
# ============================================

# Получаем путь к проекту
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

# Добавляем корень проекта в sys.path
sys.path.insert(0, project_root)

# Теперь импортируем (будет искать utils.coin_config в project_root)
try:
    from utils.coin_config import get_all_coin_types
    print("✅ Модуль coin_config успешно импортирован")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print(f"📁 Project root: {project_root}")
    print(f"📁 Содержимое папки utils:")
    utils_dir = os.path.join(project_root, 'utils')
    if os.path.exists(utils_dir):
        print(os.listdir(utils_dir))
    else:
        print("Папка utils не найдена!")
    sys.exit(1)

async def migrate_data():
    """Переносит данные из users.json в SQLite базу"""
    print("🔄 Миграция данных из users.json в SQLite...")
    print("=" * 50)

    # 1. Читаем данные из JSON
    try:
        with open('users.json', 'r', encoding='utf-8') as f:
            users_data = json.load(f)

        print(f"📊 Найдено пользователей в JSON: {len(users_data)}")
    except FileNotFoundError:
        print("❌ Файл users.json не найден")
        return
    except json.JSONDecodeError:
        print("❌ Ошибка чтения users.json")
        return

    # 2. Подключаемся к SQLite
    try:
        conn = await aiosqlite.connect('../users.db')
        print("✅ Подключение к SQLite установлено")
    except Exception as e:
        print(f"❌ Ошибка подключения к SQLite: {e}")
        return

    try:
        # 3. Очищаем существующие данные (опционально)
        clear_existing = input("Очистить существующие данные в SQLite? (y/N): ").strip().lower()
        if clear_existing == 'y':
            await conn.execute('DELETE FROM users')
            await conn.execute('DELETE FROM user_coins')
            await conn.commit()
            print("✅ Существующие данные очищены")

        # 4. Мигрируем пользователей
        migrated_count = 0
        error_count = 0

        for user_id_str, user_data in users_data.items():
            try:
                user_id = int(user_id_str)

                # Проверяем существование пользователя
                cursor = await conn.execute(
                    'SELECT COUNT(*) FROM users WHERE user_id = ?',
                    (user_id,)
                )
                result = await cursor.fetchone()

                if result[0] > 0:
                    # Пользователь уже существует
                    update_existing = input(f"Пользователь {user_id} уже существует. Обновить? (y/N): ").strip().lower()
                    if update_existing != 'y':
                        print(f"  ⏭️  Пропущен пользователь {user_id}")
                        continue

                    # Обновляем существующего пользователя
                    await conn.execute('''
                        UPDATE users 
                        SET username = ?, first_name = ?, money = ?, bronze_coin_bought = ?
                        WHERE user_id = ?
                    ''', (
                        user_data.get('username', ''),
                        user_data.get('first_name', ''),
                        float(user_data.get('money', 0)),
                        int(user_data.get('bronze_coin_bought', 0)),
                        user_id
                    ))

                    # Удаляем старые монеты
                    await conn.execute('DELETE FROM user_coins WHERE user_id = ?', (user_id,))

                else:
                    # Создаем нового пользователя
                    await conn.execute('''
                        INSERT INTO users (user_id, username, first_name, money, bronze_coin_bought)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        user_id,
                        user_data.get('username', ''),
                        user_data.get('first_name', ''),
                        float(user_data.get('money', 0)),
                        int(user_data.get('bronze_coin_bought', 0))
                    ))

                # Добавляем монеты пользователя
                coins = user_data.get('coins', {})

                # Создаем записи для всех типов монет
                for coin_type in get_all_coin_types():
                    count = int(coins.get(coin_type, 0))
                    if count > 0:
                        await conn.execute('''
                            INSERT OR REPLACE INTO user_coins (user_id, coin_type, count)
                            VALUES (?, ?, ?)
                        ''', (user_id, coin_type, count))

                migrated_count += 1
                print(f"  ✅ Мигрирован пользователь {user_id}: {user_data.get('username', 'Unknown')}")
                print(f"     Баланс: {user_data.get('money', 0)}, Монет: {len([c for c in coins.values() if c > 0])}")

                # Коммитим каждые 10 пользователей
                if migrated_count % 10 == 0:
                    await conn.commit()

            except Exception as e:
                error_count += 1
                print(f"  ❌ Ошибка миграции пользователя {user_id_str}: {e}")

        # Финальный коммит
        await conn.commit()

        print(f"\n📊 Итог миграции:")
        print(f"✅ Успешно мигрировано: {migrated_count} пользователей")
        print(f"❌ Ошибок: {error_count}")

        if migrated_count > 0:
            # Показываем статистику
            cursor = await conn.execute('SELECT COUNT(*) FROM users')
            total_users = (await cursor.fetchone())[0]

            cursor = await conn.execute('SELECT SUM(count) FROM user_coins')
            total_coins = (await cursor.fetchone())[0] or 0

            cursor = await conn.execute('SELECT SUM(money) FROM users')
            total_money = (await cursor.fetchone())[0] or 0

            print(f"\n📈 Статистика SQLite:")
            print(f"   👥 Всего пользователей: {total_users}")
            print(f"   💰 Общий баланс: {total_money:,.0f}")
            print(f"   🟤 Всего монет: {total_coins}")

    except Exception as e:
        print(f"❌ Ошибка при миграции: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await conn.close()
        print("✅ Соединение с SQLite закрыто")

    # 5. Создаем резервную копию JSON
    if migrated_count > 0:
        import shutil
        import datetime

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f'users_backup_{timestamp}.json'
        shutil.copy2('users.json', backup_path)
        print(f"\n📁 Создана резервная копия: {backup_path}")


async def verify_migration():
    """Проверяет корректность миграции"""
    print("\n🔍 Проверка миграции...")
    print("=" * 50)

    try:
        # Подключаемся к SQLite
        conn = await aiosqlite.connect('../users.db')

        # Проверяем пользователей
        cursor = await conn.execute('SELECT user_id, username, money FROM users ORDER BY money DESC LIMIT 5')
        top_users = await cursor.fetchall()

        print("🏆 Топ-5 пользователей в SQLite:")
        for i, (user_id, username, money) in enumerate(top_users, 1):
            print(f"  {i}. {username} (ID: {user_id}): {money:,.0f}")

        # Проверяем монеты
        cursor = await conn.execute('''
            SELECT u.username, uc.coin_type, uc.count 
            FROM user_coins uc
            JOIN users u ON uc.user_id = u.user_id
            WHERE uc.count > 0
            ORDER BY uc.count DESC
            LIMIT 10
        ''')
        top_coins = await cursor.fetchall()

        if top_coins:
            print("\n💰 Топ монет:")
            for username, coin_type, count in top_coins:
                print(f"  • {username}: {coin_type} ×{count}")

        await conn.close()
        print("\n✅ Проверка завершена")

    except Exception as e:
        print(f"❌ Ошибка при проверке: {e}")


async def main():
    """Основная функция"""
    print("🔄 МИГРАЦИЯ ДАННЫХ ИЗ JSON В SQLITE")
    print("=" * 50)

    # Проверяем файлы
    if not os.path.exists('users.json'):
        print("❌ Файл users.json не найден")
        return

    if not os.path.exists('../users.db'):
        print("⚠️  Файл users.db не найден, будет создан автоматически")

    # Выполняем миграцию
    await migrate_data()

    # Проверяем результат
    check = input("\nПроверить результат миграции? (Y/n): ").strip().lower()
    if check != 'n':
        await verify_migration()

    print("\n🎯 Миграция завершена!")
    print("\n🚀 Запустите бота командой: python main.py")


if __name__ == "__main__":
    import os
    import sys

    # Добавляем текущую директорию в путь
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    # Запускаем
    asyncio.run(main())