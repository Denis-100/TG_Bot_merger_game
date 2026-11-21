from utils.formatters import get_coin_display_name


def get_user_top_asset(user_data: dict) -> tuple:
    """Возвращает самый ценный актив пользователя"""
    coins = user_data.get('coins', {})

    if not coins:
        return ("Нет активов", 0)

    asset_values = {
        'diamond': 16,
        'platinum_bar': 15,
        'platinum_coin': 14,
        'ruby': 13,
        'sapphire': 12,
        'emerald': 11,
        'gold_bar': 10,
        'gold_coin': 9,
        'bronze_bar_high': 8,
        'bronze_coin_high': 7,
        'silver_bar': 6,
        'silver_coin': 5,
        'iron_bar': 4,
        'iron_coin': 3,
        'bronze_bar': 2,
        'bronze_coin': 1
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
        if "Платиновая" in display_name:
            display_name = display_name.replace("Платиновая ", "⚜️ ")
        elif "Бронзовая" in display_name:
            display_name = display_name.replace("Бронзовая ", "🟫 ")
        elif "Серебряная" in display_name:
            display_name = display_name.replace("Серебряная ", "⚪ ")
        elif "Золотая" in display_name:
            display_name = display_name.replace("Золотая ", "🟡 ")

        return (display_name, top_count)

    return ("Нет активов", 0)