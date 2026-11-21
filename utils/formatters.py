def format_number(value: float, suffix: str = "") -> str:
    """Универсальная функция форматирования чисел с русскими суффиксами"""
    if value == 0:
        return f"0{suffix}"

    # Определяем суффикс и делитель
    if value >= 1_000_000_000_000:  # триллион
        divisor = 1_000_000_000_000
        unit = " трлн"
    elif value >= 1_000_000_000:  # миллиард
        divisor = 1_000_000_000
        unit = " млрд"
    elif value >= 1_000_000:  # миллион
        divisor = 1_000_000
        unit = " млн"
    elif value >= 1_000:  # тысяча
        divisor = 1_000
        unit = " тыс"
    else:  # меньше 1000
        # Для маленьких чисел показываем с дробной частью
        if value < 1:
            return f"{value:.2f}{suffix}"
        else:
            return f"{int(value)}{suffix}"

    formatted = value / divisor

    # Для больших чисел показываем без дробной части
    if formatted >= 100:
        return f"{int(formatted)}{unit}{suffix}"
    else:
        return f"{formatted:.2f}{unit}{suffix}"


def format_price(price: float) -> str:
    """Форматирует цену для отображения"""
    return format_number(price)


def format_income(income_per_second: float) -> str:
    """Форматирует доход для отображения"""
    return format_number(income_per_second, "/сек")


def get_coin_display_name(coin_type: str) -> str:
    """Возвращает читаемое имя для типа монеты"""
    names = {
        'bronze_coin': "🟤 Медная монета",
        'bronze_bar': "🟫 Медный слиток",
        'iron_coin': "⚙️ Железная монета",
        'iron_bar': "⚙️ Железный слиток",
        'silver_coin': "⚪ Серебряная монета",
        'silver_bar': "⬜️ Серебряный слиток",
        'bronze_coin_high': "🟠 Бронзовая монета",
        'bronze_bar_high': "🟧 Бронзовый слиток",
        'gold_coin': "🟡 Золотая монета",
        'gold_bar': "🟨 Золотой слиток",
        'emerald': "💚 Изумруд",
        'sapphire': "💙 Сапфир",
        'ruby': "❤️ Рубин",
        'platinum_coin': "⚜️ Платиновая монета",
        'platinum_bar': "⚜️ Платиновый слиток",
        'diamond': "💎 Алмаз",
        'lava_coin': "🔥 Лава коин"
    }
    return names.get(coin_type, coin_type)