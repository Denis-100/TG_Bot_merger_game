# utils/exchange_logic.py
import copy
from utils.calculations import calculate_online_income
from utils.formatters import get_coin_display_name
from utils.income_config import get_exchange_rate, get_next_coin_type


def get_exchange_rules() -> dict:
    """Возвращает правила обмена монет"""
    rules = {}

    coin_types = [
        'bronze_coin', 'bronze_bar', 'iron_coin', 'iron_bar',
        'silver_coin', 'silver_bar', 'bronze_coin_high', 'bronze_bar_high',
        'gold_coin', 'gold_bar', 'emerald', 'sapphire', 'ruby',
        'platinum_coin', 'platinum_bar', 'diamond'
    ]

    for coin_type in coin_types:
        target = get_next_coin_type(coin_type)
        rate = get_exchange_rate(coin_type)

        rules[coin_type] = {
            'target': target,
            'rate': rate,
            'name': get_coin_display_name(coin_type) if coin_type != 'diamond' else 'Максимальный уровень'
        }

    return rules


async def auto_exchange_all(user: dict) -> tuple:
    """
    Автоматически объединяет все возможные монеты в более высокие ранги.
    Возвращает (новый_объект_пользователя, список_обменов, изменение_дохода_за_секунду)
    """
    new_user = copy.deepcopy(user)
    rules = get_exchange_rules()
    exchanges = []

    coin_types = [
        'bronze_coin', 'bronze_bar', 'iron_coin', 'iron_bar',
        'silver_coin', 'silver_bar', 'bronze_coin_high', 'bronze_bar_high',
        'gold_coin', 'gold_bar', 'emerald', 'sapphire', 'ruby',
        'platinum_coin', 'platinum_bar', 'diamond'
    ]

    for source_coin in coin_types:
        if source_coin in rules and rules[source_coin]['target'] is not None:
            source_count = new_user['coins'].get(source_coin, 0)
            rate = rules[source_coin]['rate']

            if source_count >= rate:
                can_exchange = source_count // rate

                if can_exchange > 0:
                    new_user['coins'][source_coin] -= can_exchange * rate
                    target_coin = rules[source_coin]['target']
                    new_user['coins'][target_coin] = new_user['coins'].get(target_coin, 0) + can_exchange

                    exchanges.append({
                        'source': source_coin,
                        'target': target_coin,
                        'source_count': can_exchange * rate,
                        'target_count': can_exchange,
                        'rate': rate,
                        'source_name': get_coin_display_name(source_coin),
                        'target_name': get_coin_display_name(target_coin)
                    })

    old_income_per_second = calculate_online_income(user)
    new_income_per_second = calculate_online_income(new_user)
    income_change_per_second = new_income_per_second - old_income_per_second

    return new_user, exchanges, income_change_per_second