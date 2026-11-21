# utils/income_config.py
"""
Файл для обратной совместимости с существующим кодом.
Версия 1.0
"""

import sys
import os

# Добавляем путь для корректного импорта
current_dir = os.path.dirname(__file__)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    # Реэкспортируем все из coin_config
    from coin_config import (
        INCOME_PER_SECOND,
        EXCHANGE_RATES,
        EXCHANGE_CHAIN,
        get_income,
        get_exchange_rate,
        get_next_coin_type,
        get_all_coin_types,
        COIN_TYPES,
        COIN_DISPLAY_NAMES,
        get_coin_display_name,
        validate_coin_config
    )

    print("✅ income_config: успешно загружен (реэкспорт из coin_config)")

except ImportError as e:
    print(f"❌ Ошибка загрузки из coin_config: {e}")

    # Заглушки на случай ошибки
    INCOME_PER_SECOND = {}
    EXCHANGE_RATES = {}
    EXCHANGE_CHAIN = []
    COIN_TYPES = []
    COIN_DISPLAY_NAMES = {}


    def get_income(coin_type: str) -> float:
        return 0


    def get_exchange_rate(coin_type: str) -> int:
        return 0


    def get_next_coin_type(coin_type: str) -> str:
        return None


    def get_all_coin_types() -> list:
        return []


    def get_coin_display_name(coin_type: str) -> str:
        return coin_type


    def validate_coin_config() -> bool:
        return False

# Список экспортируемых объектов
__all__ = [
    'INCOME_PER_SECOND',
    'EXCHANGE_RATES',
    'EXCHANGE_CHAIN',
    'get_income',
    'get_exchange_rate',
    'get_next_coin_type',
    'get_all_coin_types',
    'COIN_TYPES',
    'COIN_DISPLAY_NAMES',
    'get_coin_display_name',
    'validate_coin_config'
]