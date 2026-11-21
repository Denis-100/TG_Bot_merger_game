# Приветственные сообщения
def get_welcome_text(username: str) -> str:
    return (
        f"🎉 Добро пожаловать, {username}!\n"
        f"🌟 Вы получили подарок - первую медную монету БЕСПЛАТНО!\n"
        f"💡 Она будет приносить вам доход 1 монета в секунду.\n"
        f"Заходи в наш телеграмм канал: https://t.me/MergeToGetRich"
    )


def get_first_coin_text() -> str:
    return (
        "🎉 Поздравляем! Вы получили первую медную монету!\n"
        "🟤 Теперь у вас: 1 медная монета\n"
        "💰 Доход: 1 монета в секунду\n"
        "💡 Следующая медная монета будет стоить 10 монет."
    )


def get_no_coins_text() -> str:
    return (
        "🎁 У вас еще нет медных монет!\n"
        "Получите первую монету БЕСПЛАТНО, чтобы начать зарабатывать!"
    )


# Сообщения о покупке
def get_buy_success_text(count: int, total_price: str, new_balance: str, new_income: str,
                         price_details: str = "") -> str:
    text = (
        f"✅ Успешная покупка!\n"
        f"🟤 Куплено: {count} медных монет\n"
        f"💳 Стоимость: {total_price}\n"
        f"💰 Новый баланс: {new_balance}\n"
        f"📈 Новый доход: {new_income} в секунду"
    )
    if price_details:
        text += price_details
    return text


def get_buy_failed_text(balance: str, required: str, missing: str) -> str:
    return (
        f"❌ Недостаточно денег!\n"
        f"💰 Ваш баланс: {balance}\n"
        f"💳 Требуется: {required}\n"
        f"📉 Не хватает: {missing}"
    )


def get_buy_menu_text(balance: str, bronze_bought: int, next_price: str, income: str) -> str:
    return (
        f"💰 Ваш баланс: {balance}\n"
        f"🟤 Куплено медных монет: {bronze_bought}\n"
        f"🎯 Следующая монета: {next_price}\n"
        f"📈 Текущий доход: {income} в секунду\n"
        f"\nВыберите количество медных монет для покупки:"
    )


# Сообщения об обмене
def get_exchange_success_text(exchanges: list, old_income: str, new_income: str, income_change: str,
                              total_source: int, total_target: int, exchange_count: int) -> str:
    from utils.parse_num import parse_formatted_number
    text = "✅ Автоматический обмен выполнен!\n\n📊 Результаты обмена:\n"

    for exchange in exchanges:
        text += f"• {exchange['source_name']} → {exchange['target_name']}: {exchange['source_count']} → {exchange['target_count']}\n"

    text += f"\n📈 Изменение дохода:\n"
    text += f"• Было: {old_income} в секунду\n"
    text += f"• Стало: {new_income} в секунду\n"

    income_change_value = parse_formatted_number(income_change)

    if income_change_value > 0:
        text += f"• Увеличение: +{income_change} в секунду\n"
    elif income_change_value < 0:
        clean_change = income_change.replace('-', '').strip()
        text += f"• Уменьшение: {clean_change} в секунду\n"
    else:
        text += f"• Доход не изменился\n"

    text += f"\n📦 Итоги:\n"
    text += f"• Потрачено монет: {total_source}\n"
    text += f"• Получено активов: {total_target}\n"
    text += f"• Всего обменов: {exchange_count}\n"

    return text


def get_no_exchange_text(user_coins: dict) -> str:
    """
    Универсальная функция для отображения статуса всех монет.
    Автоматически определяет иерархию, сортирует в правильном порядке и нумерует.
    """
    try:
        from utils.exchange_logic import get_exchange_rules
        from utils.formatters import get_coin_display_name
        from utils.coin_config import COIN_TYPES  # Импортируем порядок из конфига

        rules = get_exchange_rules()

        # Определяем порядок монет: сначала из COIN_TYPES, затем остальные
        ordered_coins = []

        # 1. Добавляем монеты в порядке из COIN_TYPES
        for coin_type in COIN_TYPES:
            if coin_type in rules or coin_type in user_coins:
                ordered_coins.append(coin_type)

        # 2. Добавляем остальные монеты (например, lava_coin)
        all_coins = set(user_coins.keys()) | set(rules.keys())
        for coin_type in sorted(all_coins):
            if coin_type not in ordered_coins:
                ordered_coins.append(coin_type)

        # Автоматически определяем максимальные монеты (у которых нет target)
        max_coins_types = [coin for coin, rule in rules.items()
                           if rule.get('target') is None]

        # Группируем монеты
        result_lines = []
        max_coin_number = None

        for idx, coin_type in enumerate(ordered_coins, 1):
            count = user_coins.get(coin_type, 0)

            # Получаем красивое имя
            try:
                display_name = get_coin_display_name(coin_type)
            except:
                display_name = ' '.join(word.capitalize()
                                        for word in coin_type.split('_'))

            # Определяем статус монеты
            if coin_type in max_coins_types:
                # Максимальная монета - запоминаем номер
                max_coin_number = idx
                if count > 0:
                    result_lines.append(f"{idx}. {display_name}: {count} 🏆 МАКСИМУМ")
                else:
                    result_lines.append(f"{idx}. {display_name}: {count} 🔥 Финальная цель")
            elif coin_type in rules:
                # Монета с обменом
                rule = rules[coin_type]
                rate = rule.get('rate', 3)
                if count <= rate:
                    needed = rate - count
                    result_lines.append(f"{idx}. {display_name}: {count}/{rate}")
            else:
                # Простая монета без правил
                if count > 0:
                    result_lines.append(f"{idx}. {display_name}: {count}")
                else:
                    result_lines.append(f"{idx}. {display_name}: {count}")

        # Формируем итоговый текст
        output = "\n📊 Статус ваших монет:\n" + "\n".join(result_lines)

        # Добавляем общую статистику
        total_max = sum(user_coins.get(coin, 0) for coin in max_coins_types)
        if total_max > 0:
            output += f"\n\n🎉 Вы достигли максимума с {total_max} монет(ами) на уровне {max_coin_number}!"

        return output

    except ImportError as e:
        # Fallback если модули не найдены
        result_lines = []
        for idx, (coin, count) in enumerate(sorted(user_coins.items()), 1):
            result_lines.append(f"{idx}. {coin}: {count}")

        return f"\n📊 Ваши монеты:\n" + "\n".join(result_lines)


# Сообщения таблицы лидеров
def get_leaderboard_text(sorted_users: list, user_position: int = 0,
                         user_data: dict = None, text: str = "✨ ТОП-10 ИГРОКОВ ✨\n",
                         sort_by: str = "money") -> str:
    from utils.formatters import format_price, get_coin_display_name

    text += "•" * 42 + "\n\n"

    for i, (user_id_str, user_data_item) in enumerate(sorted_users[:10], 1):
        first_name = user_data_item.get('first_name', '')
        if not first_name:
            username = user_data_item.get('username', '')
            first_name = username.split('_')[0].split('.')[0] if username else f"Игрок{i}"

        first_name = first_name.strip()[:15]

        money = user_data_item.get('money', 0)
        bronze_bought = user_data_item.get('bronze_coin_bought', 0)

        from database.user_data import get_user_top_asset
        top_asset_name, top_asset_count = get_user_top_asset(user_data_item)

        place_emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"][i - 1]

        text += f"{place_emoji} {first_name}\n"
        if sort_by == "money":
            # Если сортируем по деньгам - показываем баланс первым
            text += f"   Баланс: {format_price(money)}\n"
            text += f"   Куплено медных: {bronze_bought}\n"
        else:
            # Если сортируем по монетам - показываем монеты первым
            text += f"   Куплено медных: {bronze_bought}\n"
            text += f"   Баланс: {format_price(money)}\n"

        if top_asset_count > 0:
            if " " in top_asset_name:
                parts = top_asset_name.split()
                asset_short = f"{parts[0]} {parts[-1]}"
            else:
                asset_short = top_asset_name
            text += f"   Лучший актив: {asset_short} ×{top_asset_count}\n"

        if i < len(sorted_users[:10]):
            text += "   ───────────────────\n\n"
        else:
            text += "\n"

    text += "─" * 35 + "\n\n"

    if user_position > 0 and user_data:
        text += f"🎯 ВАША ПОЗИЦИЯ: {user_position}\n"

        if sort_by == "money":
            text += f"💰 Баланс: {format_price(user_data.get('money', 0))}\n"
            text += f"🟤 Медных: {user_data.get('bronze_coin_bought', 0)}\n"
        else:
            text += f"🟤 Медных: {user_data.get('bronze_coin_bought', 0)}\n"
            text += f"💰 Баланс: {format_price(user_data.get('money', 0))}\n"

        top_asset_name, top_asset_count = get_user_top_asset(user_data)
        if top_asset_count > 0:
            if " " in top_asset_name:
                parts = top_asset_name.split()
                asset_short = f"{parts[0]} {parts[-1]}"
            else:
                asset_short = top_asset_name
            text += f"💎 Лучший актив: {asset_short} ×{top_asset_count}\n"

        if user_position > 1:
            user_above = sorted_users[user_position - 2]

            if sort_by == "money":
                # Разница в деньгах
                money_above = user_above[1].get('money', 0)
                need_more = money_above - user_data.get('money', 0) + 1
                if need_more > 0:
                    text += f"\n📈 До {user_position - 1} места: +{format_price(need_more)} денег"
            else:
                # Разница в монетах
                bronze_above = user_above[1].get('bronze_coin_bought', 0)
                need_more_bronze = bronze_above - user_data.get('bronze_coin_bought', 0) + 1
                if need_more_bronze > 0:
                    text += f"\n📈 До {user_position - 1} места: +{need_more_bronze} медных монет"

    text += f"\n📊 Всего игроков: {len(sorted_users)}"
    return text


def get_no_users_text() -> str:
    return "📭 В базе данных пока нет пользователей."


# Общие сообщения
def get_price_details_text(preview: list, bronze_bought: int) -> str:
    from utils.formatters import format_price

    text = "💰 Цены следующих медных монет:\n\n"

    for coin_number, price in preview:
        price_text = "БЕСПЛАТНО" if price == 0 else format_price(price)
        if coin_number == bronze_bought + 1:
            text += f"{coin_number}. {price_text} (следующая)\n"
        else:
            text += f"{coin_number}. {price_text}\n"

    text += f"\n📊 Статистика:\n"
    text += f"• Уже куплено: {bronze_bought} монет\n"
    text += f"• Цена следующей: {format_price(preview[0][1])}\n"
    text += f"• Цена 10-й сл. монеты: {format_price(preview[9][1])}\n"

    return text


def get_back_to_menu_text() -> str:
    return "Меню"


def get_default_message_text() -> str:
    return "Привет! Напиши '/start' для запуска!"
