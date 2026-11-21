# database/user_data.py
from utils.coin_config import get_coin_display_name


def get_user_top_asset(user_data: dict) -> tuple:
    """Возвращает самый ценный актив пользователя"""
    coins = user_data.get('coins', {})

    if not coins:
        return ("Нет активов", 0)

    # Значимость активов (чем выше число, тем ценнее)
    asset_values = {
        'lava_coin': 17,  # 🔥 Лава коин - самый ценный
        'diamond': 16,  # 💎 Алмаз
        'platinum_bar': 15,  # ⚜️ Платиновый слиток
        'platinum_coin': 14,  # ⚜️ Платиновая монета
        'ruby': 13,  # ❤️ Рубин
        'sapphire': 12,  # 💙 Сапфир
        'emerald': 11,  # 💚 Изумруд
        'gold_bar': 10,  # 🟡 Золотой слиток
        'gold_coin': 9,  # 🟡 Золотая монета
        'bronze_bar_high': 8,  # 🟫 Бронзовый слиток (высший сорт)
        'bronze_coin_high': 7,  # 🟫 Бронзовая монета (высший сорт)
        'silver_bar': 6,  # ⬜️ Серебряный слиток
        'silver_coin': 5,  # ⚪ Серебряная монета
        'iron_bar': 4,  # ⚙️ Железный слиток
        'iron_coin': 3,  # ⚙️ Железная монета
        'bronze_bar': 2,  # 🟤 Медный слиток
        'bronze_coin': 1  # 🟤 Медная монета
    }

    top_asset = None
    top_count = 0
    max_value = 0

    for coin_type, count in coins.items():
        if count > 0:
            value = asset_values.get(coin_type, 0)
            if value > max_value:
                max_value = value
                top_asset = coin_type
                top_count = count
            elif value == max_value and count > top_count:
                top_asset = coin_type
                top_count = count

    if top_asset:
        display_name = get_coin_display_name(top_asset)
        return (display_name, top_count)

    return ("Нет активов", 0)


def get_user_total_income(user_data: dict) -> float:
    """Возвращает общий доход пользователя в секунду"""
    from utils.calculations import calculate_online_income
    return calculate_online_income(user_data)


def get_user_coin_summary(user_data: dict) -> str:
    """Возвращает краткую сводку по монетам пользователя"""
    coins = user_data.get('coins', {})

    if not coins:
        return "Нет монет"

    # Считаем только ненулевые монеты
    active_coins = {k: v for k, v in coins.items() if v > 0}

    if not active_coins:
        return "Нет активных монет"

    # Сортируем по ценности
    from utils.coin_config import get_all_coin_types
    coin_order = {coin: i for i, coin in enumerate(get_all_coin_types())}

    sorted_coins = sorted(
        active_coins.items(),
        key=lambda x: coin_order.get(x[0], 1000),
        reverse=True  # Самые ценные первыми
    )

    # Формируем строку (максимум 3 самые ценные монеты)
    result = []
    for coin_type, count in sorted_coins[:3]:
        display_name = get_coin_display_name(coin_type)
        # Укорачиваем длинные названия
        if len(display_name) > 15:
            parts = display_name.split()
            if len(parts) > 2:
                display_name = f"{parts[0]} {parts[-1]}"
        result.append(f"{display_name} ×{count}")

    return ", ".join(result)