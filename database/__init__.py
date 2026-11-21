# database/__init__.py
import os
import sys

# Получаем конфигурацию из config
try:
    from config import DB_TYPE, SQLITE_PATH, DATABASE_URL, ENVIRONMENT
except ImportError as e:
    print(f"❌ Ошибка импорта config: {e}")
    print("   Устанавливаем значения по умолчанию...")
    DB_TYPE = 'sqlite'
    SQLITE_PATH = 'users.db'
    DATABASE_URL = 'sqlite:///users.db'
    ENVIRONMENT = 'development'

print(f"🗄️ Инициализация БД:")
print(f"  Тип: {DB_TYPE}")
print(f"  Окружение: {ENVIRONMENT}")

# Загружаем соответствующий менеджер БД
try:
    if DB_TYPE == 'postgresql':
        from .db_manager import db
        print("✅ PostgreSQL менеджер загружен")
    else:
        from .sqlite_manager import SQLiteDatabase
        db = SQLiteDatabase(SQLITE_PATH)
        print(f"✅ SQLite менеджер загружен: {SQLITE_PATH}")
        
except ImportError as e:
    print(f"❌ Ошибка импорта менеджера БД: {e}")
    sys.exit(1)

__all__ = ['db', 'DB_TYPE', 'SQLITE_PATH', 'DATABASE_URL', 'ENVIRONMENT']
