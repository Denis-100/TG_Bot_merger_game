# Приветственные сообщения
def get_welcome_text(username: str) -> str:
    return (
        f"🎉 Добро пожаловать, {username}!\n"
        f"🌟 Вы получили подарок - первую медную монету БЕСПЛАТНО!\n"
        f"💡 Она будет приносить вам доход 1 монета в секунду."
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
    text = "✅ Автоматический обмен выполнен!\n\n📊 Результаты обмена:\n"

    for exchange in exchanges:
        text += f"• {exchange['source_name']} → {exchange['target_name']}: {exchange['source_count']} → {exchange['target_count']}\n"

    text += f"\n📈 Изменение дохода:\n"
    text += f"• Было: {old_income} в секунду\n"
    text += f"• Стало: {new_income} в секунду\n"

    if float(income_change.replace('K', '000').replace('M', '000000').replace('B', '000000000')) > 0:
        text += f"• Увеличение: +{income_change} в секунду\n"
    elif float(income_change.replace('K', '000').replace('M', '000000').replace('B', '000000000')) < 0:
        text += f"• Уменьшение: {income_change} в секунду\n"
    else:
        text += f"• Доход не изменился\n"

    text += f"\n📦 Итоги:\n"
    text += f"• Потрачено монет: {total_source}\n"
    text += f"• Получено активов: {total_target}\n"
    text += f"• Всего обменов: {exchange_count}\n"

    return text


def get_no_exchange_text(user_coins: dict) -> str:
    from utils.exchange_logic import get_exchange_rules
    rules = get_exchange_rules()
    needed_info = "\n💡 Для обмена нужно:\n"

    for source_coin, rule in rules.items():
        if rule['target'] is not None:
            source_count = user_coins.get(source_coin, 0)
            if source_count < rule['rate']:
                needed = rule['rate'] - source_count
                if needed > 0:
                    from utils.formatters import get_coin_display_name
                    source_name = get_coin_display_name(source_coin)
                    target_name = rule['name']
                    needed_info += f"• {source_name}: {source_count}/{rule['rate']} (нужно ещё {needed})\n"

    return (
        f"❌ Нет доступных обменов!\n"
        f"💡 Нужно минимум 3 монеты одного типа для объединения.\n"
        f"{needed_info}"
    )


# Сообщения таблицы лидеров
def get_leaderboard_text(sorted_users: list, user_position: int = 0, user_data: dict = None) -> str:
    from utils.formatters import format_price, get_coin_display_name

    text = "✨ ТОП-10 ИГРОКОВ ✨\n"
    text += "•" * 35 + "\n\n"

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
        text += f"   Баланс: {format_price(money)}\n"
        text += f"   Куплено медных: {bronze_bought}\n"

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
        text += f"💰 Баланс: {format_price(user_data.get('money', 0))}\n"
        text += f"🟤 Медных: {user_data.get('bronze_coin_bought', 0)}\n"

        top_asset_name, top_asset_count = get_user_top_asset(user_data)
        if top_asset_count > 0:
            if " " in top_asset_name:
                parts = top_asset_name.split()
                asset_short = f"{parts[0]} {parts[-1]}"
            else:
                asset_short = top_asset_name
            text += f"💎 Актив: {asset_short} ×{top_asset_count}\n"

        if user_position > 1:
            user_above = sorted_users[user_position - 2]
            money_above = user_above[1].get('money', 0)
            need_more = money_above - user_data.get('money', 0) + 1

            if need_more > 0:
                text += f"\n📈 До {user_position - 1} места: +{format_price(need_more)}"

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