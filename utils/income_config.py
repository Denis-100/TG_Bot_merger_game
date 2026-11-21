# utils/income_config.py
"""
Централизованная конфигурация доходов от всех активов.
Все изменения в доходах нужно вносить только здесь!
"""

# Доход в секунду для каждого типа актива
INCOME_PER_SECOND = {
    'bronze_coin': 1,
    'bronze_bar': 5,
    'iron_coin': 23,
    'iron_bar': 104,
    'silver_coin': 468,
    'silver_bar': 2106,
    'bronze_coin_high': 9447,
    'bronze_bar_high': 42647,
    'gold_coin': 191900,
    'gold_bar': 863600,
    'emerald': 3886000,
    'sapphire': 17480000,
    'ruby': 78690000,
    'platinum_coin': 354100000,
    'platinum_bar': 1593000000,
    'diamond': 50000000000
}

# Обменный курс для объединения (сколько нужно для получения следующего уровня)
EXCHANGE_RATES = {
    'bronze_coin': 3,  # 3 медные монеты = 1 медный слиток
    'bronze_bar': 3,  # 3 медных слитка = 1 железная монета
    'iron_coin': 3,  # 3 железные монеты = 1 железный слиток
    'iron_bar': 3,  # 3 железных слитка = 1 серебряная монета
    'silver_coin': 3,  # 3 серебряные монеты = 1 серебряный слиток
    'silver_bar': 3,  # 3 серебряных слитка = 1 бронзовая монета (высший сорт)
    'bronze_coin_high': 3,  # 3 бронзовые монеты = 1 бронзовый слиток
    'bronze_bar_high': 3,  # 3 бронзовых слитка = 1 золотая монета
    'gold_coin': 3,  # 3 золотые монеты = 1 золотой слиток
    'gold_bar': 3,  # 3 золотых слитка = 1 изумруд
    'emerald': 3,  # 3 изумруда = 1 сапфир
    'sapphire': 3,  # 3 сапфира = 1 рубин
    'ruby': 3,  # 3 рубина = 1 платиновая монета
    'platinum_coin': 3,  # 3 платиновые монеты = 1 платиновый слиток
    'platinum_bar': 3,  # 3 платиновых слитка = 1 алмаз
    'diamond': 0  # Максимальный уровень, дальше не обменивается
}

# Порядок обмена (цепочка улучшений)
EXCHANGE_CHAIN = [
    'bronze_coin',  # 0
    'bronze_bar',  # 1
    'iron_coin',  # 2
    'iron_bar',  # 3
    'silver_coin',  # 4
    'silver_bar',  # 5
    'bronze_coin_high',  # 6
    'bronze_bar_high',  # 7
    'gold_coin',  # 8
    'gold_bar',  # 9
    'emerald',  # 10
    'sapphire',  # 11
    'ruby',  # 12
    'platinum_coin',  # 13
    'platinum_bar',  # 14
    'diamond'  # 15
]


def get_income(coin_type: str) -> float:
    """Возвращает доход для указанного типа монеты"""
    return INCOME_PER_SECOND.get(coin_type, 0)


def get_exchange_rate(coin_type: str) -> int:
    """Возвращает обменный курс для указанного типа монеты"""
    return EXCHANGE_RATES.get(coin_type, 0)


def get_next_coin_type(coin_type: str) -> str:
    """Возвращает следующий тип монеты в цепочке улучшений"""
    if coin_type not in EXCHANGE_CHAIN:
        return None

    index = EXCHANGE_CHAIN.index(coin_type)
    if index + 1 < len(EXCHANGE_CHAIN):
        return EXCHANGE_CHAIN[index + 1]
    return None