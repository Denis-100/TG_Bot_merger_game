import os
import asyncio
import json
import aiofiles
from typing import Dict, Any
from config import DATA_FILE


class DataManager:
    """Менеджер для безопасной работы с данными пользователей"""

    def __init__(self):
        self.lock = asyncio.Lock()

    async def read_data(self) -> Dict:
        """Безопасное чтение данных с блокировкой"""
        async with self.lock:
            if not os.path.exists(DATA_FILE):
                return {}

            try:
                async with aiofiles.open(DATA_FILE, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    return json.loads(content) if content else {}
            except (json.JSONDecodeError, FileNotFoundError):
                return {}

    async def write_data(self, data: Dict) -> None:
        """Безопасная запись данных с блокировкой"""
        async with self.lock:
            async with aiofiles.open(DATA_FILE, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, indent=4, ensure_ascii=False))

    async def update_user(self, user_id: int, update_func) -> Dict[str, Any]:
        """Атомарное обновление пользователя"""
        async with self.lock:
            data = await self.read_data()
            user_id_str = str(user_id)

            if user_id_str not in data:
                return None

            # Получаем текущие данные пользователя
            user_data = data[user_id_str]

            # Применяем функцию обновления
            updated_user = update_func(user_data)

            # Сохраняем обновленные данные
            data[user_id_str] = updated_user
            await self.write_data(data)

            return updated_user


# Создаем глобальный экземпляр менеджера
data_manager = DataManager()