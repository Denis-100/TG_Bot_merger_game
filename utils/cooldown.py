# utils/cooldown_simple.py
"""
Простая система задержки для кнопок
"""
from datetime import datetime, timedelta
from typing import Dict

# Храним время последнего нажатия: {user_id: timestamp}
_last_click: Dict[int, datetime] = {}


def check_cooldown(user_id: int, seconds: int = 1) -> bool:
    """
    Проверяет, прошла ли задержка

    :return: True если можно нажимать, False если задержка не прошла
    """
    now = datetime.now()

    if user_id in _last_click:
        last_time = _last_click[user_id]
        if now - last_time < timedelta(seconds=seconds):
            return False

    _last_click[user_id] = now
    return True