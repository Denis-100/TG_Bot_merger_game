from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from utils.calculations import calculate_bronze_coin_price, should_show_advanced_buttons
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


def get_buy_coins_keyboard(user_data: dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    bronze_bought = user_data.get('bronze_coin_bought', 0)
    show_advanced = should_show_advanced_buttons(user_data)

    # Всегда показываем кнопку покупки 3 монет
    total_price_3 = calculate_bronze_coin_price(user_data, 3)
    button_text_3 = f"Купить 3 медные монеты"
    if total_price_3 > 0:
        button_text_3 += f" - {format_price(total_price_3)}"
    else:
        button_text_3 += " - БЕСПЛАТНО"

    builder.row(InlineKeyboardButton(text=button_text_3, callback_data="buy_bronze_3"))

    if show_advanced:
        # Продвинутые кнопки для богатых игроков
        advanced_quantities = [1, 100, 500, 2500, 10000]

        # Первая строка: 1 монета
        price_1 = calculate_bronze_coin_price(user_data, 1)
        button_text_1 = "1 шт" + (f" - {format_price(price_1)}" if price_1 > 0 else " - БЕСПЛАТНО")
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

    # Дополнительные кнопки
    builder.row(InlineKeyboardButton(text="📊 Цены следующих монет", callback_data="price_details"))
    builder.row(InlineKeyboardButton(text="↩️ Назад в меню", callback_data="back_to_menu"))

    return builder.as_markup()


def get_leaderboard_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_leaderboard"))
    return builder.as_markup()