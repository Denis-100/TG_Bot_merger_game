import os
import sys
from dotenv import load_dotenv


def clean_env_value(value: str) -> str:
    """Убирает кавычки из значения переменной окружения"""
    if not value:
        return value

    # Убираем кавычки в начале и конце
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or \
            (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]

    return value


# Определяем окружение
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

print(f"⚙️  Загрузка конфигурации. Окружение: {ENVIRONMENT}")

# Загружаем соответствующий файл
if ENVIRONMENT == "development":
    if os.path.exists('.env.local'):
        load_dotenv('.env.local', override=True)
        print("✅ Загружен .env.local для разработки")
    elif os.path.exists('.env'):
        load_dotenv('.env', override=True)
        print("⚠️  .env.local не найден, загружен .env")
    else:
        print("⚠️  Файлы .env не найдены")
else:
    if os.path.exists('.env'):
        load_dotenv('.env', override=True)
        print("✅ Загружен .env для продакшена")
    else:
        print("⚠️  .env не найден")

# Теперь получаем значения
BOT_TOKEN = clean_env_value(os.getenv("BOT_TOKEN"))
DATABASE_URL = clean_env_value(os.getenv("DATABASE_URL"))

if not BOT_TOKEN:
    print("❌ BOT_TOKEN не найден!")
    print("   Установите токен в .env или .env.local")
    sys.exit(1)

if not DATABASE_URL:
    print("⚠️  DATABASE_URL не найден, использую SQLite по умолчанию")
    DATABASE_URL = 'sqlite:///users.db'

# Определяем тип базы данных по URL
if DATABASE_URL and DATABASE_URL.startswith('postgresql://'):
    DB_TYPE = 'postgresql'
elif DATABASE_URL and DATABASE_URL.startswith('sqlite:///'):
    DB_TYPE = 'sqlite'
    # Извлекаем путь к файлу SQLite
    SQLITE_PATH = DATABASE_URL.replace('sqlite:///', '')
else:
    DB_TYPE = 'sqlite'  # По умолчанию для разработки
    SQLITE_PATH = 'users.db'
    DATABASE_URL = f'sqlite:///{SQLITE_PATH}'

print(f"🔧 Окружение: {ENVIRONMENT}")
print(f"🗄️ Тип БД: {DB_TYPE}")
print(f"🤖 Токен: {BOT_TOKEN[:10]}...")
print(f"🔗 DATABASE_URL: {DATABASE_URL[:40]}...")