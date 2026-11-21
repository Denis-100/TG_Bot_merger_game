# handlers/main_handlers.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from database import db
from keyboards.reply_kb import get_main_keyboard, get_help_menu
from keyboards.inline_kb import get_first_coin_keyboard, get_buy_coins_keyboard, get_leaderboard_keyboard
from texts.messages import *
from texts.help_texts import *
from texts.profile_texts import get_profile_text
from utils.calculations import (
    calculate_bronze_coin_price, calculate_coin_income,
    calculate_online_income, get_price_breakdown, get_next_prices_preview
)
from utils.formatters import format_price, get_coin_display_name
from utils.coin_config import get_all_coin_types, get_coin_display_name as get_coin_name
from utils.exchange_logic import auto_exchange_all
from database.user_data import get_user_top_asset

router = Router()


def ensure_user_income(user: dict) -> dict:
    """Гарантирует наличие online_income в данных пользователя"""
    if 'online_income' not in user:
        user['online_income'] = calculate_online_income(user)
    return user


# ========== ОСНОВНЫЕ ОБРАБОТЧИКИ ==========
@router.message(Command("start"))
async def start_menu(message: Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.first_name or message.from_user.username or "Пользователь"

    # Получаем пользователя
    user = await db.get_or_create_user(user_id, username)

    # Проверяем, есть ли у пользователя первая монета
    if user['coins'].get('bronze_coin', 0) == 0 and user['bronze_coin_bought'] == 0:
        await message.answer(
            get_welcome_text(username),
            reply_markup=get_first_coin_keyboard()
        )
    else:
        await message.answer("Меню", reply_markup=get_main_keyboard())
        await message.answer(f"С возвращением, {username}!")


@router.callback_query(F.data == "first_free_coin")
async def get_first_free_coin(callback: CallbackQuery):
    """Обработчик получения первой бесплатной монеты"""
    user_id = callback.from_user.id
    username = callback.from_user.username or callback.from_user.first_name or "Пользователь"

    # Получаем пользователя
    user = await db.get_or_create_user(user_id, username)

    # Добавляем первую медную монету
    coins = user['coins'].copy()
    coins['bronze_coin'] = coins.get('bronze_coin', 0) + 1

    # Обновляем данные
    await db.update_user_coins(user_id, coins)
    await db.update_bronze_bought(user_id, 1)

    await callback.message.answer(get_first_coin_text(), reply_markup=get_main_keyboard())
    await callback.answer()


@router.message(F.text == "💼 Профиль")
async def profile(message: Message):
    """Обработчик кнопки Профиль"""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name or "Пользователь"

    # Получаем пользователя
    user = await db.get_or_create_user(user_id, username)
    user = ensure_user_income(user)

    next_price = calculate_bronze_coin_price(user, 1)

    coins_list = []
    for coin_type in get_all_coin_types():
        count = user['coins'].get(coin_type, 0)
        if count > 0:
            display_name = get_coin_name(coin_type)
            income_per_sec = calculate_coin_income(coin_type, count)
            coins_list.append(f"  {display_name}: {count} (+{format_price(income_per_sec)}/сек)")

    await message.answer(get_profile_text(user, str(next_price), coins_list))


@router.message(F.text == "❓ Помощь")
async def help_command(message: Message):
    """Обработчик кнопки ❓ Помощь - показывает меню помощи"""
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
    await message.answer("Меню", reply_markup=get_main_keyboard())


# ========== ПОКУПКА МОНЕТ ==========
@router.message(F.text == "🛒 Купить медные монеты")
async def buy_coin_menu(message: Message):
    """Обработчик кнопки Купить медные монеты"""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name or "Пользователь"

    # Получаем пользователя
    user = await db.get_or_create_user(user_id, username)
    user = ensure_user_income(user)

    if user['bronze_coin_bought'] == 0:
        await message.answer(get_no_coins_text(), reply_markup=get_first_coin_keyboard())
        return

    next_price = calculate_bronze_coin_price(user, 1)

    await message.answer(
        get_buy_menu_text(
            format_price(user['money']),
            user['bronze_coin_bought'],
            format_price(next_price),
            format_price(user['online_income'])  # Используем уже рассчитанный доход
        ),
        reply_markup=get_buy_coins_keyboard(user)
    )


@router.callback_query(lambda c: c.data.startswith("buy_bronze"))
async def buy_bronze_coins(callback: CallbackQuery):
    """Обработчик покупки медных монет"""
    user_id = callback.from_user.id
    username = callback.from_user.username or callback.from_user.first_name or "Пользователь"

    try:
        # Парсим количество монет из callback_data
        data_parts = callback.data.split("_")
        count = int(data_parts[-1]) if len(data_parts) > 2 else 1

        # Получаем пользователя
        user = await db.get_or_create_user(user_id, username)
        user = ensure_user_income(user)

        # Рассчитываем стоимость
        total_price = calculate_bronze_coin_price(user, count)

        # Проверяем баланс
        if user['money'] >= total_price or total_price == 0:
            prices = get_price_breakdown(user, count)

            if total_price > 0:
                # Вычитаем стоимость
                new_balance = user['money'] - total_price
                await db.update_user_money(user_id, new_balance)

            # Добавляем монеты
            coins = user['coins'].copy()
            coins['bronze_coin'] = coins.get('bronze_coin', 0) + count

            # Обновляем монеты и количество купленных
            await db.update_user_coins(user_id, coins)
            await db.update_bronze_bought(user_id, user['bronze_coin_bought'] + count)

            # Получаем обновленные данные для расчета дохода
            updated_user = await db.get_or_create_user(user_id, username)
            updated_user = ensure_user_income(updated_user)

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
                    format_price(updated_user['money']),
                    format_price(updated_user['online_income']),
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
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


@router.callback_query(F.data == "price_details")
async def show_price_details(callback: CallbackQuery):
    """Обработчик показа деталей цен"""
    user_id = callback.from_user.id
    username = callback.from_user.username or callback.from_user.first_name or "Пользователь"

    # Получаем пользователя
    user = await db.get_or_create_user(user_id, username)

    preview = get_next_prices_preview(user, 10)

    await callback.message.answer(get_price_details_text(preview, user['bronze_coin_bought']))
    await callback.answer()


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    """Обработчик возврата в меню"""
    await callback.message.answer(get_back_to_menu_text(), reply_markup=get_main_keyboard())
    await callback.answer()


# ========== ОБМЕН МОНЕТ ==========
@router.message(F.text == "🔄 Обменять монеты")
async def exchange_coins(message: Message):
    """Обработчик кнопки 🔄 Обменять монеты"""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name or "Пользователь"

    # Получаем пользователя
    user = await db.get_or_create_user(user_id, username)
    user = ensure_user_income(user)

    old_income_per_second = calculate_online_income(user)

    # Выполняем автоматический обмен
    new_user, exchanges, income_change_per_second = await auto_exchange_all(user)

    if not exchanges:
        await message.answer(get_no_exchange_text(user['coins']))
        return

    # Сохраняем обновленные данные
    await db.update_user_coins(user_id, new_user['coins'])

    # Получаем обновленные данные для расчета нового дохода
    updated_user = await db.get_or_create_user(user_id, username)
    updated_user = ensure_user_income(updated_user)
    new_income_per_second = calculate_online_income(updated_user)

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
async def show_leaderboard_command(message: Message, rating_type: str = "money", user_id: int = None):
    """Обработчик показа таблицы лидеров"""
    try:
        # Получаем всех пользователей
        users_data = await db.get_all_users()
        target_user_id = user_id if user_id is not None else message.from_user.id

        if not users_data:
            await message.answer(get_no_users_text())
            return

        # Сортируем в зависимости от типа рейтинга
        if rating_type == "coins":
            # Сортируем по количеству купленных медных монет
            sorted_users_data = sorted(
                users_data,
                key=lambda x: x.get('bronze_coin_bought', 0),
                reverse=True
            )
            rating_title = "🏅 Топ по купленным монетам"
        else:
            # По умолчанию сортируем по деньгам
            sorted_users_data = sorted(
                users_data,
                key=lambda x: x.get('money', 0),
                reverse=True
            )
            rating_title = "💰 Топ по деньгам"

        # Преобразуем данные
        sorted_users = []
        for user_data in sorted_users_data:
            user_data = ensure_user_income(user_data)
            sorted_users.append((str(user_data['user_id']), user_data))

        user_id = target_user_id
        user_id_str = str(user_id)
        user_position = 0
        current_user_data = None

        # Находим позицию текущего пользователя
        for i, (uid, user_data) in enumerate(sorted_users, 1):
            if uid == user_id_str:
                user_position = i
                current_user_data = user_data
                break

        # Если пользователя нет в списке, получаем его данные
        if not current_user_data:
            username = message.from_user.username or message.from_user.first_name or "Пользователь"
            current_user_data = await db.get_or_create_user(user_id, username)
            current_user_data = ensure_user_income(current_user_data)

            # Ищем позицию в зависимости от типа рейтинга
            for i, (_, user_data) in enumerate(sorted_users, 1):
                if rating_type == "coins":
                    if user_data.get('bronze_coin_bought', 0) < current_user_data.get('bronze_coin_bought', 0):
                        user_position = i
                        break
                else:  # money
                    if user_data.get('money', 0) < current_user_data.get('money', 0):
                        user_position = i
                        break
            else:
                user_position = len(sorted_users) + 1

        # Отправляем сообщение с соответствующей клавиатурой
        await message.answer(
            get_leaderboard_text(
                sorted_users,
                user_position,
                current_user_data
            ),
            reply_markup=get_leaderboard_keyboard(rating_type)
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка при загрузке таблицы лидеров: {str(e)}")


@router.callback_query(F.data.startswith("leaderboard_"))
async def leaderboard_callback_handler(callback: CallbackQuery):
    """Обработчик callback для переключения между типами рейтинга"""
    try:
        data = callback.data

        if data == "leaderboard_money":
            await callback.message.delete()  # Удаляем старое сообщение
            await show_leaderboard_command(callback.message, rating_type="money", user_id=callback.from_user.id)

        elif data == "leaderboard_coins":
            await callback.message.delete()  # Удаляем старое сообщение
            await show_leaderboard_command(callback.message, rating_type="coins", user_id=callback.from_user.id)

        elif data == "leaderboard_back":
            await callback.message.delete()  # Удаляем старое сообщение
            await callback.message.answer(
                "🏠 Возвращаемся в главное меню",
                reply_markup=get_main_keyboard()
            )

        await callback.answer()
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


@router.callback_query(F.data == "refresh_leaderboard")
async def refresh_leaderboard(callback: CallbackQuery):
    """Обработчик обновления таблицы лидеров"""
    try:
        # Удаляем старое сообщение
        await callback.message.delete()

        # Получаем всех пользователей
        sorted_users_data = await db.get_all_users()

        if not sorted_users_data:
            await callback.message.answer(get_no_users_text())
            return

        # Преобразуем данные в формат для функции get_leaderboard_text
        sorted_users = []
        for user_data in sorted_users_data:
            user_data = ensure_user_income(user_data)
            sorted_users.append((str(user_data['user_id']), user_data))

        user_id = callback.from_user.id
        user_id_str = str(user_id)
        user_position = 0
        current_user_data = None

        # Находим позицию текущего пользователя
        for i, (uid, user_data) in enumerate(sorted_users, 1):
            if uid == user_id_str:
                user_position = i
                current_user_data = user_data
                break

        # Если пользователя нет в списке, получаем его данные
        if not current_user_data:
            username = callback.from_user.username or callback.from_user.first_name or "Пользователь"
            current_user_data = await db.get_or_create_user(user_id, username)
            current_user_data = ensure_user_income(current_user_data)

            # Ищем позицию среди всех пользователей
            for i, (_, user_data) in enumerate(sorted_users, 1):
                if user_data['money'] < current_user_data['money']:
                    user_position = i
                    break
            else:
                user_position = len(sorted_users) + 1

        await callback.message.answer(
            get_leaderboard_text(sorted_users, user_position, current_user_data),
            reply_markup=get_leaderboard_keyboard()
        )

        await callback.answer()
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка при обновлении таблицы лидеров: {str(e)}")
        await callback.answer()


# ========== ОБРАБОТКА ВСЕХ ОСТАЛЬНЫХ СООБЩЕНИЙ ==========
@router.message()
async def handle_all_messages(message: Message):
    """Обработчик всех остальных сообщений"""
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username or first_name or "Пользователь"

    # Обновляем имя пользователя, если оно изменилось
    if first_name:
        # Сначала получаем текущие данные
        user = await db.get_or_create_user(user_id, username)

        # Проверяем, изменилось ли имя
        if user['first_name'] != first_name:
            # Обновляем имя пользователя
            await db.update_user(user_id, {'first_name': first_name})

    # Список команд, которые мы обрабатываем
    processed_commands = [
        "Профиль", "🛒 Купить медные монеты", "🔄 Обменять монеты",
        "🏆 Таблица игроков", "❓ Помощь", "Справка по боту",
        "Команды", "Советы", "Активы в игре", "↩️ Назад в меню"
    ]

    if message.text not in processed_commands:
        if not message.text.startswith('/'):
            await message.answer(get_default_message_text())

@router.message(Command("top_money"))
@router.message(F.text == "💰 Топ по деньгам")
async def show_money_top(message: Message):
    """Показывает топ по деньгам"""
    await show_leaderboard_command(message, rating_type="money")

@router.message(Command("top_coins"))
@router.message(F.text == "🪙 Топ по монетам")
async def show_coins_top(message: Message):
    """Показывает топ по купленным монетам"""
    await show_leaderboard_command(message, rating_type="coins")


print("✅ handlers/main_handlers.py загружен успешно")