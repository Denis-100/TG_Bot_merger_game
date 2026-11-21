# config.py
import os
import sys

ADMINS = [1029698029]

def get_env_var(name, default=None):
    """Безопасное получение переменной окружения"""
    value = os.getenv(name)
    if not value:
        return default
    
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]
    
    return value

# Основные переменные
BOT_TOKEN = get_env_var("BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ BOT_TOKEN не найден!")
    print("   Установите в Railway: Settings → Variables")
    sys.exit(1)

DATABASE_URL = get_env_var("DATABASE_URL", "sqlite:///users.db")
ENVIRONMENT = get_env_var("ENVIRONMENT", "development")

# Определяем тип БД
if DATABASE_URL and DATABASE_URL.startswith('postgresql://'):
    DB_TYPE = 'postgresql'
    SQLITE_PATH = None
elif DATABASE_URL and DATABASE_URL.startswith('sqlite:///'):
    DB_TYPE = 'sqlite'
    SQLITE_PATH = DATABASE_URL.replace('sqlite:///', '')
else:
    DB_TYPE = 'sqlite'
    SQLITE_PATH = 'users.db'

print(f"⚙️ Конфигурация:")
print(f"  Окружение: {ENVIRONMENT}")
print(f"  Тип БД: {DB_TYPE}")
print(f"  Токен: {BOT_TOKEN[:10]}...")
if DB_TYPE == 'postgresql':
    print(f"  PostgreSQL URL: {DATABASE_URL[:50]}...")
else:
    print(f"  SQLite файл: {SQLITE_PATH}")

# Экспортируем ВСЕ переменные
__all__ = ['BOT_TOKEN', 'DATABASE_URL', 'ENVIRONMENT', 'DB_TYPE', 'SQLITE_PATH']
