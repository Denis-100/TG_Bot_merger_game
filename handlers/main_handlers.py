from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from database.async_db import (
    get_user_data, save_user_data, update_user_first_name,
    get_sorted_users, income_loop
)
from keyboards.reply_kb import get_main_menu, get_help_menu
from keyboards.inline_kb import (
    get_first_coin_keyboard, get_buy_coins_keyboard,
    get_leaderboard_keyboard
)
from texts.messages import *
from texts.help_texts import *
from texts.profile_texts import get_profile_text
from utils.calculations import (
    calculate_bronze_coin_price, calculate_coin_income,
    calculate_online_income, get_price_breakdown,
    get_next_prices_preview
)
from utils.formatters import format_price, get_coin_display_name
from utils.exchange_logic import auto_exchange_all

router = Router()


# ========== ОСНОВНЫЕ ОБРАБОТЧИКИ ==========
@router.message(Command("start"))
async def start_menu(message: Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username or "Пользователь"
    user = await get_user_data(user_id, username)

    if user['coins']['bronze_coin'] == 0 and user['bronze_coin_bought'] == 0:
        await message.answer(
            get_welcome_text(message.from_user.username or "Пользователь"),
            reply_markup=get_first_coin_keyboard()
        )
    else:
        await message.answer("Меню", reply_markup=get_main_menu())
        await message.answer(f"С возвращением, {message.from_user.username or 'Пользователь'}!")


@router.callback_query(F.data == "first_free_coin")
async def get_first_free_coin(callback: CallbackQuery):
    """Обработчик получения первой бесплатной монеты"""
    user_id = callback.from_user.id
    username = callback.from_user.username or "Пользователь"
    user = await get_user_data(user_id, username)

    user['coins']['bronze_coin'] += 1
    user['bronze_coin_bought'] = 1
    await save_user_data(user_id, user)

    await callback.message.answer(get_first_coin_text(), reply_markup=get_main_menu())
    await callback.answer()


@router.message(F.text == "Профиль")
async def profile(message: Message):
    """Обработчик кнопки Профиль"""
    user_id = message.from_user.id
    username = message.from_user.username or "Пользователь"
    user = await get_user_data(user_id, username)

    next_price = calculate_bronze_coin_price(user, 1)

    coins_list = []
    for coin_type, count in user['coins'].items():
        if count > 0:
            display_name = get_coin_display_name(coin_type)
            income_per_sec = calculate_coin_income(coin_type, count)
            coins_list.append(f"  {display_name}: {count} (+{format_price(income_per_sec)}/сек)")

    await message.answer(get_profile_text(user, str(next_price), coins_list))


@router.message(F.text == "Помощь")
async def help_command(message: Message):
    """Обработчик кнопки Помощь - показывает меню помощи"""
    await message.answer(get_help_main_text(), reply_markup=get_help_menu())


@router.message(F.text == "Справка по боту")
async def bot_info(message: Message):
    """Обработчик кнопки Справка по боту"""
    await message.answer(get_bot_info_text(), reply_markup=get_help_menu())


@router.message(F.text == "Команды")
async def commands_info(message: Message):
    """Обработчик кнопки Команды"""
    await message.answer(get_commands_text(), reply_markup=get_help_menu())


@router.message(F.text == "Советы")
async def tips_info(message: Message):
    """Обработчик кнопки Советы"""
    await message.answer(get_tips_text(), reply_markup=get_help_menu())


@router.message(F.text == "Активы в игре")
async def assets_info(message: Message):
    """Обработчик кнопки Активы в игре"""
    await message.answer(get_assets_info_text(), reply_markup=get_help_menu())


@router.message(F.text == "↩️ Назад в меню")
async def back_to_main_menu(message: Message):
    """Обработчик кнопки Назад в меню"""
    await message.answer("Меню", reply_markup=get_main_menu())


# ========== ПОКУПКА МОНЕТ ==========
@router.message(F.text == "Купить медные монеты")
async def buy_coin_menu(message: Message):
    """Обработчик кнопки Купить медные монеты"""
    user_id = message.from_user.id
    username = message.from_user.username or "Пользователь"
    user = await get_user_data(user_id, username)

    if user['bronze_coin_bought'] == 0:
        await message.answer(get_no_coins_text(), reply_markup=get_first_coin_keyboard())
        return

    next_price = calculate_bronze_coin_price(user, 1)

    await message.answer(
        get_buy_menu_text(
            format_price(user['money']),
            user['bronze_coin_bought'],
            format_price(next_price),
            format_price(user['online_income'])
        ),
        reply_markup=get_buy_coins_keyboard(user)
    )


@router.callback_query(lambda c: c.data.startswith("buy_bronze"))
async def buy_bronze_coins(callback: CallbackQuery):
    """Обработчик покупки медных монет"""
    user_id = callback.from_user.id
    username = callback.from_user.username or "Пользователь"
    count = int(callback.data.split("_")[-1])

    user = await get_user_data(user_id, username)
    total_price = calculate_bronze_coin_price(user, count)

    if user['money'] >= total_price or total_price == 0:
        prices = get_price_breakdown(user, count)

        if total_price > 0:
            user['money'] -= total_price

        user['coins']['bronze_coin'] += count
        user['bronze_coin_bought'] += count

        await save_user_data(user_id, user)

        price_details = ""
        if count <= 5:
            price_details = "\n📋 Цены поштучно:\n"
            for i, price in enumerate(prices, 1):
                price_text = "БЕСПЛАТНО" if price == 0 else format_price(price)
                price_details += f"  {i}. {price_text}\n"

        await callback.message.answer(
            get_buy_success_text(
                count,
                format_price(total_price),
                format_price(user['money']),
                format_price(user['online_income']),
                price_details
            )
        )
    else:
        await callback.message.answer(
            get_buy_failed_text(
                format_price(user['money']),
                format_price(total_price),
                format_price(total_price - user['money'])
            )
        )

    await callback.answer()


@router.callback_query(F.data == "price_details")
async def show_price_details(callback: CallbackQuery):
    """Обработчик показа деталей цен"""
    user_id = callback.from_user.id
    username = callback.from_user.username or "Пользователь"
    user = await get_user_data(user_id, username)

    preview = get_next_prices_preview(user, 10)

    await callback.message.answer(get_price_details_text(preview, user['bronze_coin_bought']))
    await callback.answer()


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    """Обработчик возврата в меню"""
    await callback.message.answer(get_back_to_menu_text(), reply_markup=get_main_menu())
    await callback.answer()


# ========== ОБМЕН МОНЕТ ==========
@router.message(F.text == "Обменять монеты")
async def exchange_coins(message: Message):
    """Обработчик кнопки Обменять монеты"""
    user_id = message.from_user.id
    username = message.from_user.username or "Пользователь"
    user = await get_user_data(user_id, username)

    old_income_per_second = calculate_online_income(user)

    new_user, exchanges, income_change_per_second = await auto_exchange_all(user)

    if not exchanges:
        await message.answer(get_no_exchange_text(user['coins']))
        return

    await save_user_data(user_id, new_user)

    new_income_per_second = calculate_online_income(new_user)

    total_source_used = sum(exchange['source_count'] for exchange in exchanges)
    total_target_gained = sum(exchange['target_count'] for exchange in exchanges)

    await message.answer(
        get_exchange_success_text(
            exchanges,
            format_price(old_income_per_second),
            format_price(new_income_per_second),
            format_price(income_change_per_second),
            total_source_used,
            total_target_gained,
            len(exchanges)
        )
    )


# ========== ТАБЛИЦА ЛИДЕРОВ ==========
@router.message(Command("top"))
@router.message(Command("игроки"))
@router.message(Command("players"))
@router.message(F.text == "🏆 Таблица игроков")
async def show_leaderboard_command(message: Message):
    """Обработчик показа таблицы лидеров"""
    sorted_users = await get_sorted_users()

    if not sorted_users:
        await message.answer(get_no_users_text())
        return

    user_id = str(message.from_user.id)
    user_position = 0
    current_user_data = None

    for i, (uid, user_data) in enumerate(sorted_users, 1):
        if uid == user_id:
            user_position = i
            current_user_data = user_data
            break

    await message.answer(
        get_leaderboard_text(sorted_users, user_position, current_user_data),
        reply_markup=get_leaderboard_keyboard()
    )


@router.callback_query(F.data == "refresh_leaderboard")
async def refresh_leaderboard(callback: CallbackQuery):
    """Обработчик обновления таблицы лидеров"""
    await callback.message.delete()

    # Повторяем логику показа таблицы лидеров
    sorted_users = await get_sorted_users()

    if not sorted_users:
        await callback.message.answer(get_no_users_text())
        return

    user_id = str(callback.from_user.id)
    user_position = 0
    current_user_data = None

    for i, (uid, user_data) in enumerate(sorted_users, 1):
        if uid == user_id:
            user_position = i
            current_user_data = user_data
            break

    await callback.message.answer(
        get_leaderboard_text(sorted_users, user_position, current_user_data),
        reply_markup=get_leaderboard_keyboard()
    )

    await callback.answer()


@router.message()
async def handle_all_messages(message: Message):
    """Обработчик всех остальных сообщений"""
    user_id = message.from_user.id
    first_name = message.from_user.first_name

    if first_name:
        await update_user_first_name(user_id, first_name)

    # Список команд, которые мы обрабатываем
    processed_commands = [
        "Профиль", "Купить медные монеты", "Обменять монеты",
        "🏆 Таблица игроков", "Помощь", "Справка по боту",
        "Команды", "Советы", "Активы в игре", "↩️ Назад в меню"
    ]

    if message.text not in processed_commands:
        if not message.text.startswith('/'):
            await message.answer(get_default_message_text())