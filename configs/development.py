# configs/development.py
"""
Конфигурация для локальной разработки
"""

# Использовать SQLite для разработки
USE_SQLITE = True

# Использовать фиктивные данные для тестирования
USE_MOCK_DATA = False

# Логирование в файл
LOG_TO_FILE = True
LOG_FILE = "bot_dev.log"

# Период начисления дохода (для разработки можно увеличить)
INCOME_INTERVAL = 5  # секунд