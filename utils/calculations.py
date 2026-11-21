from utils.coin_config import get_income


def calculate_coin_income(coin_type: str, count: int) -> float:
    """Рассчитывает доход для конкретного типа монеты и количества"""
    income_per_second = get_income(coin_type)
    return count * income_per_second


def calculate_online_income(user: dict) -> float:
    """Рассчитывает онлайн доход на основе всех типов монет"""
    total_income = 0
    for coin_type, count in user.get('coins', {}).items():
        total_income += calculate_coin_income(coin_type, count)

    return total_income


def calculate_bronze_coin_price(user: dict, quantity: int = 1) -> float:
    """Рассчитывает стоимость покупки указанного количества медных монет"""
    bronze_bought = user.get('bronze_coin_bought', 0)
    total_price = 0

    for i in range(quantity):
        price_for_coin = 0
        if bronze_bought + i > 0:
            price_for_coin = 10 + (bronze_bought + i - 1) * 15
        total_price += price_for_coin

    return total_price


def get_price_breakdown(user: dict, quantity: int) -> list:
    """Возвращает детальную информацию о ценах"""
    bronze_bought = user.get('bronze_coin_bought', 0)
    prices = []

    for i in range(quantity):
        price = 0
        if bronze_bought + i > 0:
            price = 10 + (bronze_bought + i - 1) * 15
        prices.append(price)

    return prices


def get_next_prices_preview(user: dict, count: int = 10) -> list:
    """Возвращает цены следующих count монет"""
    bronze_bought = user.get('bronze_coin_bought', 0)
    preview = []

    for i in range(count):
        price = 0
        if bronze_bought + i > 0:
            price = 10 + (bronze_bought + i - 1) * 15
        preview.append((bronze_bought + i + 1, price))

    return preview


def should_show_advanced_buttons(user: dict) -> bool:
    """Определяет, нужно ли показывать продвинутые кнопки покупки"""
    return user.get('money', 0) >= 100_000_000  # 100 миллионов