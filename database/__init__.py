# database/__init__.py
import os
import sys
from config import DB_TYPE, SQLITE_PATH

print(f"🗄️ Инициализация БД. Тип: {DB_TYPE}")
print(f"📁 Путь SQLite: {SQLITE_PATH}")

if DB_TYPE == 'postgresql':
    try:
        from .db_manager import db
        print("🚀 Используется PostgreSQL")
    except ImportError as e:
        print(f"❌ Ошибка импорта PostgreSQL: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка PostgreSQL: {e}")
        sys.exit(1)
elif DB_TYPE == 'sqlite':
    try:
        from .sqlite_manager import db
        print(f"🔧 Используется SQLite")
    except ImportError as e:
        print(f"❌ Ошибка импорта SQLite: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка SQLite: {e}")
        sys.exit(1)
else:
    print(f"❌ Неизвестный тип БД: {DB_TYPE}")
    sys.exit(1)

__all__ = ['db']