def format_price(price: float) -> str:
    """Форматирует цену для отображения"""
    if price == 0:
        return "0"
    elif price >= 1000000000:  # 1B+
        return f"{price / 1000000000:.3f}B"
    elif price >= 1000000:  # 1M+
        return f"{price / 1000000:.3f}M"
    elif price >= 1000:  # 1K+
        return f"{price / 1000:.3f}K"
    else:
        return f"{int(price)}"

def format_income(income_per_second: float) -> str:
    """Форматирует доход для отображения"""
    if income_per_second >= 1000000000:  # 1B+
        return f"{income_per_second/1000000000:.3f}B/сек"
    elif income_per_second >= 1000000:   # 1M+
        return f"{income_per_second/1000000:.3f}M/сек"
    elif income_per_second >= 1000:      # 1K+
        return f"{income_per_second/1000:.3f}K/сек"
    else:                             # любое число
        return f"{income_per_second:.1f}/сек"

def get_coin_display_name(coin_type: str) -> str:
    """Возвращает читаемое имя для типа монеты"""
    names = {
        'bronze_coin': "🟤 Медная монета",
        'bronze_bar': "🟤 Медный слиток",
        'iron_coin': "⚙️ Железная монета",
        'iron_bar': "⚙️ Железный слиток",
        'silver_coin': "⚪ Серебряная монета",
        'silver_bar': "⚪ Серебряный слиток",
        'bronze_coin_high': "🟫 Бронзовая монета",
        'bronze_bar_high': "🟫 Бронзовый слиток",
        'gold_coin': "🟡 Золотая монета",
        'gold_bar': "🟡 Золотой слиток",
        'emerald': "💚 Изумруд",
        'sapphire': "💙 Сапфир",
        'ruby': "❤️ Рубин",
        'platinum_coin': "⚜️ Платиновая монета",
        'platinum_bar': "⚜️ Платиновый слиток",
        'diamond': "💎 Алмаз"
    }
    return names.get(coin_type, coin_type)