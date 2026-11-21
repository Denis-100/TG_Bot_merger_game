from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from utils.calculations import calculate_bronze_coin_price, should_show_advanced_buttons, should_show_super_advanced_buttons
from utils.formatters import format_price


def get_first_coin_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🎁 Получить первую БЕСПЛАТНУЮ монету!",
            callback_data="first_free_coin"
        )
    )
    return builder.as_markup()


def get_buy_coins_keyboard(user_data: dict, message_id: int = None) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для покупки монет

    :param user_data: Данные пользователя
    :param message_id: ID сообщения для обновления (опционально)
    :return: InlineKeyboardMarkup
    """
    builder = InlineKeyboardBuilder()

    bronze_bought = user_data.get('bronze_coin_bought', 0)
    show_advanced = should_show_advanced_buttons(user_data)
    show_super_advanced = should_show_super_advanced_buttons(user_data)

    # Всегда показываем кнопку покупки 3 монет
    if not show_super_advanced:
        total_price_3 = calculate_bronze_coin_price(user_data, 3)
        button_text_3 = f"Купить 3 медные монеты"
        if total_price_3 > 0:
            button_text_3 += f" - {format_price(total_price_3)}"
        else:
            button_text_3 += " - БЕСПЛАТНО"

        builder.row(InlineKeyboardButton(text=button_text_3, callback_data="buy_bronze_3"))

    if show_advanced and not show_super_advanced:
        # Продвинутые кнопки для богатых игроков
        advanced_quantities = [1, 100, 500, 2500, 10000]

        # Первая строка: 1 монета
        price_1 = calculate_bronze_coin_price(user_data, 1)
        button_text_1 = "1 🟤" + (f" - {format_price(price_1)}" if price_1 > 0 else " - БЕСПЛАТНО")
        builder.row(InlineKeyboardButton(text=button_text_1, callback_data="buy_bronze_1"))

        # Вторая строка: 100, 500
        row_buttons_100_500 = []
        for qty in [100, 500]:
            total_price = calculate_bronze_coin_price(user_data, qty)
            button_text = f"{qty} шт - {format_price(total_price)}"
            row_buttons_100_500.append(
                InlineKeyboardButton(text=button_text, callback_data=f"buy_bronze_{qty}")
            )
        builder.row(*row_buttons_100_500)

        # Третья строка: 2500, 10000
        row_buttons_2500_10000 = []
        for qty in [2500, 10000]:
            total_price = calculate_bronze_coin_price(user_data, qty)
            button_text = f"{qty} шт - {format_price(total_price)}"
            row_buttons_2500_10000.append(
                InlineKeyboardButton(text=button_text, callback_data=f"buy_bronze_{qty}")
            )
        builder.row(*row_buttons_2500_10000)

    elif show_super_advanced:
        # Первая строка: 100, 500
        row_buttons_100_500 = []
        for qty in [100, 500]:
            total_price = calculate_bronze_coin_price(user_data, qty)
            button_text = f"{qty} шт - {format_price(total_price)}"
            row_buttons_100_500.append(
                InlineKeyboardButton(text=button_text, callback_data=f"buy_bronze_{qty}")
            )
        builder.row(*row_buttons_100_500)

        # Вторая строка: 2500, 10000
        row_buttons_2500_10000 = []
        for qty in [2500, 10000]:
            total_price = calculate_bronze_coin_price(user_data, qty)
            button_text = f"{qty} шт - {format_price(total_price)}"
            row_buttons_2500_10000.append(
                InlineKeyboardButton(text=button_text, callback_data=f"buy_bronze_{qty}")
            )
        builder.row(*row_buttons_2500_10000)

        # Третья строка: 100 000
        total_price = calculate_bronze_coin_price(user_data, 100000)
        button_text = f"100 000 шт - {format_price(total_price)}"
        builder.row(InlineKeyboardButton(text=button_text, callback_data=f"buy_bronze_{100000}"))
    else:
        # Стандартные кнопки для новых игроков
        if bronze_bought < 5:
            quantities = [1, 5, 10]
        elif bronze_bought < 20:
            quantities = [1, 5, 10, 25]
        else:
            quantities = [1, 10, 25, 50, 100]

        row_buttons = []
        for qty in quantities:
            total_price = calculate_bronze_coin_price(user_data, qty)
            button_text = f"{qty} шт"
            if total_price > 0:
                button_text += f" - {format_price(total_price)}"
            else:
                button_text += " - БЕСПЛАТНО"

            row_buttons.append(InlineKeyboardButton(text=button_text, callback_data=f"buy_bronze_{qty}"))

        # Добавляем кнопки по 2 в ряд
        for i in range(0, len(row_buttons), 2):
            if i + 1 < len(row_buttons):
                builder.row(row_buttons[i], row_buttons[i + 1])
            else:
                builder.row(row_buttons[i])

    # Кнопка "Обновить" с передачей message_id для удаления
    refresh_data = f"refresh_buy_menu:{message_id}" if message_id else "refresh_buy_menu"
    builder.row(InlineKeyboardButton(text="🔄 Обновить", callback_data=refresh_data))

    # Дополнительные кнопки
    builder.row(InlineKeyboardButton(text="↩️ Назад в меню", callback_data="back_to_menu"))

    return builder.as_markup()


def get_leaderboard_text(sorted_users, user_position, current_user_data,
                         rating_type="money", title="💰 Топ по деньгам") -> str:
    """Генерирует текст таблицы лидеров для разных типов рейтинга"""

    text = f"{title}\n"
    text += f"👥 Всего игроков: {len(sorted_users)}\n\n"

    # Определяем ключ для отображения значения
    if rating_type == "coins":
        value_key = "bronze_coin_bought"
        value_suffix = " 🟤"
    else:  # money
        value_key = "money"
        value_suffix = " 💰"

    # Топ-10 игроков
    text += "🏆 ТОП-10 ИГРОКОВ:\n"

    for i, (user_id_str, user_data) in enumerate(sorted_users[:10], 1):
        username = user_data.get('username', f"Игрок {user_id_str}")
        first_name = user_data.get('first_name', '')
        display_name = username if username else first_name

        if rating_type == "coins":
            value = user_data.get('bronze_coin_bought', 0)
            display_value = f"{value:,}{value_suffix}"
        else:  # money
            value = user_data.get('money', 0)
            display_value = format_price(value)

        # Медали для первых трех мест
        medal = ""
        if i == 1:
            medal = "🥇 "
        elif i == 2:
            medal = "🥈 "
        elif i == 3:
            medal = "🥉 "

        # Обрезаем слишком длинные имена
        if len(display_name) > 15:
            display_name = display_name[:12] + "..."

        text += f"{medal}{i}. {display_name} - {display_value}\n"

    # Позиция текущего пользователя
    text += f"\n📊 ВАША ПОЗИЦИЯ: #{user_position}\n"

    if rating_type == "coins":
        user_value = (current_user_data.get('bronze_coin_bought', 0))
        text += f"🟤 Куплено медных монет: {user_value}\n"

        # Прогресс до следующей позиции
        if user_position > 1 and len(sorted_users) > 1:
            above_user = sorted_users[user_position - 2][1]  # Пользователь выше
            above_value = above_user.get('bronze_coin_bought', 0)
            needed = above_value - user_value + 1
            text += f"📈 До #{user_position - 1} нужно: {needed:,} монет\n"

        # Прогресс до следующей позиции
        if user_position > 1 and len(sorted_users) > 1:
            above_user = sorted_users[user_position - 2][1]
            above_total = sum(above_user.get('coins', {}).values())
            needed = above_total - above_user.get('coins', {}).values() + 1
            text += f"📈 До #{user_position - 1} нужно: {needed:,} монет\n"

    else:  # money
        user_money = current_user_data.get('money', 0)
        text += f"💰 Ваш баланс: {format_price(user_money)}\n"

        # Прогресс до следующей позиции
        if user_position > 1 and len(sorted_users) > 1:
            above_user = sorted_users[user_position - 2][1]
            above_money = above_user.get('money', 0)
            needed = above_money - user_money + 1
            text += f"📈 До #{user_position - 1} нужно: {format_price(needed)}\n"

    # Статистика (если есть данные)
    if sorted_users:
        if rating_type == "coins":
            top_value = sorted_users[0][1].get('bronze_coin_bought', 0)
            text += f"\n🥇 Лидер: {top_value:,} монет"
        else:  # money
            top_money = sorted_users[0][1].get('money', 0)
            text += f"\n🥇 Лидер: {format_price(top_money)}"

    text += "\n\nДанные обновляются при каждом открытии"

    return text


def get_leaderboard_keyboard(rating_type="money") -> InlineKeyboardMarkup:
    """Создает клавиатуру для таблицы лидеров"""
    builder = InlineKeyboardBuilder()

    # Кнопки переключения между рейтингами
    buttons = []

    money_text = "💰 Деньги" if rating_type != "money" else "✅ Деньги"
    coins_text = "🟤 Монеты" if rating_type != "coins" else "✅ Монеты"

    buttons.append(InlineKeyboardButton(text=money_text, callback_data="leaderboard_money"))
    buttons.append(InlineKeyboardButton(text=coins_text, callback_data="leaderboard_coins"))

    builder.row(*buttons)
    builder.row(InlineKeyboardButton(text="↩️ Назад в меню", callback_data="leaderboard_back"))

    return builder.as_markup()
