import copy
from utils.calculations import calculate_online_income
from utils.coin_config import (
    get_exchange_rate,
    get_next_coin_type,
    get_coin_display_name,
    get_all_coin_types
)


def get_exchange_rules() -> dict:
    """Возвращает правила обмена монет"""
    rules = {}

    for coin_type in get_all_coin_types():
        target = get_next_coin_type(coin_type)
        rate = get_exchange_rate(coin_type)

        rules[coin_type] = {
            'target': target,
            'rate': rate,
            'name': get_coin_display_name(coin_type) if coin_type != 'lava_coin' else 'Максимальный уровень'
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

    # Используем все типы монет из конфига
    for coin_type in get_all_coin_types():
        if coin_type in rules and rules[coin_type]['target'] is not None:
            source_count = new_user['coins'].get(coin_type, 0)
            rate = rules[coin_type]['rate']

            if source_count >= rate:
                can_exchange = source_count // rate

                if can_exchange > 0:
                    new_user['coins'][coin_type] -= can_exchange * rate
                    target_coin = rules[coin_type]['target']
                    new_user['coins'][target_coin] = new_user['coins'].get(target_coin, 0) + can_exchange

                    exchanges.append({
                        'source': coin_type,
                        'target': target_coin,
                        'source_count': can_exchange * rate,
                        'target_count': can_exchange,
                        'rate': rate,
                        'source_name': get_coin_display_name(coin_type),
                        'target_name': get_coin_display_name(target_coin)
                    })

    old_income_per_second = calculate_online_income(user)
    new_income_per_second = calculate_online_income(new_user)
    income_change_per_second = new_income_per_second - old_income_per_second

    return new_user, exchanges, income_change_per_second