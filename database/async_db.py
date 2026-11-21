import asyncio
import os
import json
import aiofiles
from typing import Dict, Any, List, Tuple
from config import DATA_FILE
from utils.calculations import calculate_online_income
from .data_manager import data_manager
import shutil
import datetime


async def create_backup() -> str:
    """Создает резервную копию файла данных"""
    if not os.path.exists(DATA_FILE):
        return None

    backup_dir = "backups"
    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_dir, f"users_backup_{timestamp}.json")

    shutil.copy2(DATA_FILE, backup_file)
    return backup_file


async def restore_backup(backup_file: str) -> bool:
    """Восстанавливает данные из резервной копии"""
    if not os.path.exists(backup_file):
        return False

    shutil.copy2(backup_file, DATA_FILE)
    return True


async def read_users_file() -> Dict:
    """Асинхронное чтение файла с пользователями"""
    return await data_manager.read_data()


async def write_users_file(data: Dict) -> None:
    """Асинхронная запись в файл пользователей"""
    await data_manager.write_data(data)


async def get_user_data(user_id: int, username: str) -> Dict[str, Any]:
    """Асинхронное получение данных пользователя"""
    data = await read_users_file()
    user_id_str = str(user_id)

    if user_id_str not in data:
        data[user_id_str] = {
            "username": username,
            "first_name": "",
            "money": 0,
            "coins": {
                "bronze_coin": 0,
                "bronze_bar": 0,
                "iron_coin": 0,
                "iron_bar": 0,
                "silver_coin": 0,
                "silver_bar": 0,
                "bronze_coin_high": 0,
                "bronze_bar_high": 0,
                "gold_coin": 0,
                "gold_bar": 0,
                "emerald": 0,
                "sapphire": 0,
                "ruby": 0,
                "platinum_coin": 0,
                "platinum_bar": 0,
                "diamond": 0
            },
            "bronze_coin_bought": 0,
            "online_income": 0
        }
        # Сохраняем весь словарь с новым пользователем
        await write_users_file(data)

    user_data = data[user_id_str]

    # Гарантируем правильные типы данных
    user_data['money'] = float(user_data.get('money', 0))
    user_data['bronze_coin_bought'] = int(user_data.get('bronze_coin_bought', 0))

    # Гарантируем, что все значения в coins являются целыми числами
    for coin_type in user_data['coins']:
        user_data['coins'][coin_type] = int(user_data['coins'].get(coin_type, 0))

    # Рассчитываем и обновляем доход
    user_data['online_income'] = calculate_online_income(user_data)

    return user_data


async def save_user_data(user_id: int, user_data: Dict[str, Any]) -> None:
    """Асинхронное сохранение данных пользователя"""
    data = await read_users_file()
    user_id_str = str(user_id)

    # Рассчитываем доход перед сохранением
    user_data['online_income'] = calculate_online_income(user_data)

    # Гарантируем правильные типы данных
    user_data['money'] = float(user_data.get('money', 0))
    user_data['bronze_coin_bought'] = int(user_data.get('bronze_coin_bought', 0))

    # Гарантируем, что все значения в coins являются целыми числами
    for coin_type in user_data['coins']:
        user_data['coins'][coin_type] = int(user_data['coins'].get(coin_type, 0))

    # Сохраняем данные пользователя
    data[user_id_str] = user_data
    await write_users_file(data)


async def update_user_first_name(user_id: int, first_name: str) -> bool:
    """Асинхронное обновление имени пользователя"""
    if not first_name or not first_name.strip():
        return False

    data = await read_users_file()
    user_id_str = str(user_id)

    if user_id_str in data:
        data[user_id_str]['first_name'] = first_name.strip()
        await write_users_file(data)
        return True

    return False


async def get_all_users() -> Dict:
    """Асинхронное получение всех пользователей"""
    return await read_users_file()


async def get_sorted_users() -> List[Tuple[str, Dict]]:
    """Асинхронное получение отсортированных пользователей"""
    users = await read_users_file()
    return sorted(
        users.items(),
        key=lambda x: x[1].get('money', 0),
        reverse=True
    )


async def income_loop() -> None:
    """Асинхронный цикл начисления дохода"""
    while True:
        try:
            data = await read_users_file()

            for user_id_str, user_data in data.items():
                total_income = user_data.get('online_income', 0)
                user_data['money'] += total_income

            await write_users_file(data)
        except Exception as e:
            print(f"Ошибка в income_loop: {e}")

        await asyncio.sleep(1)