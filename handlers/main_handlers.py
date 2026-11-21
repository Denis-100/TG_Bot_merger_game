# handlers/main_handlers.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

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
from utils.cooldown import check_cooldown
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


# ========== СТАРТ И БЕСПЛАТНАЯ МОНЕТА ==========
class Start:
    @router.message(Command("start"))
    async def start_menu(message: Message):
        """Обработчик команды /start"""
        user_id = message.from_user.id
        username = message.from_user.first_name or message.from_user.username or "Пользователь"

        # Получаем пользователя
        user = await db.get_or_create_user(user_id, username)

        # Проверяем, есть ли у пользователя первая монета
        if user['coins'].get('bronze_coin', 0) == 0 and user['bronze_coin_bought'] == 0:
            await message.answer(get_bot_info_text())
            await message.answer(get_commands_text())
            await message.answer(
                get_welcome_text(username),
                reply_markup=get_first_coin_keyboard()
            )
        else:
            await message.answer(f"С возвращением, {username}!")
            await message.answer("Меню", reply_markup=get_main_keyboard())


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


# ========== ГЛАВНОЕ МЕНЮ ==========
class MenuButton:
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


    @router.message(Command("help"))
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
class BuyCoin:
    last_shop_messages = {}
    last_purchase_messages = {}

    # ▼▼▼ ДОБАВИЛ: Функция обновления меню покупки ▼▼▼
    @staticmethod
    async def refresh_buy_menu(callback: CallbackQuery):
        """Обновляет меню покупки монет"""
        user_id = callback.from_user.id

        # Получаем актуальные данные пользователя
        username = callback.from_user.username or callback.from_user.first_name or "Пользователь"
        user = await db.get_or_create_user(user_id, username)
        user = ensure_user_income(user)

        # Обновляем текст меню
        next_price = calculate_bronze_coin_price(user, 1)
        menu_text = get_buy_menu_text(
            format_price(user['money']),
            user['bronze_coin_bought'],
            format_price(next_price),
            format_price(user['online_income'])
        )

        # Создаем новую клавиатуру с ID текущего сообщения для удаления
        keyboard = get_buy_coins_keyboard(user, callback.message.message_id)
        try:
            # Редактируем текущее сообщение
            await callback.message.edit_text(
                text=menu_text,
                reply_markup=keyboard
            )
            await callback.answer("✅ Меню обновлено!")
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                await callback.answer("✅ Данные уже актуальны!")
            else:
                raise e

    # ▲▲▲ КОНЕЦ ДОБАВЛЕНИЯ ▲▲▲

    @staticmethod
    @router.message(F.text == "🛒 Купить медные монеты")
    async def buy_coin_menu(message: Message):
        """Обработчик кнопки купить медные монеты"""
        user_id = message.from_user.id
        if user_id in BuyCoin.last_purchase_messages:
            del BuyCoin.last_purchase_messages[user_id]

        if user_id in BuyCoin.last_shop_messages:
            try:
                await message.bot.delete_message(
                    chat_id=user_id,
                    message_id=BuyCoin.last_shop_messages[user_id]
                )
            except:
                pass

        username = message.from_user.username or message.from_user.first_name or "Пользователь"

        # Получаем пользователя
        user = await db.get_or_create_user(user_id, username)
        user = ensure_user_income(user)

        if user['bronze_coin_bought'] == 0:
            await message.answer(get_no_coins_text(), reply_markup=get_first_coin_keyboard())
            return

        next_price = calculate_bronze_coin_price(user, 1)

        # СОХРАНЯЕМ ID СООБЩЕНИЯ С МЕНЮ
        shop_message = await message.answer(
            get_buy_menu_text(
                format_price(user['money']),
                user['bronze_coin_bought'],
                format_price(next_price),
                format_price(user['online_income'])
            ),
            reply_markup=get_buy_coins_keyboard(user)  # ← клавиатура с ценами
        )

        BuyCoin.last_shop_messages[user_id] = shop_message.message_id  # ← СОХРАНИЛИ ID

    @staticmethod
    @router.callback_query(lambda c: c.data.startswith("buy_bronze"))
    async def buy_bronze_coins(callback: CallbackQuery):
        """Обработчик покупки медных монет"""
        user_id = callback.from_user.id

        if not check_cooldown(user_id, seconds=2):
            await callback.answer("⏳ Подождите 2 секунды перед следующей покупкой", show_alert=True)
            return

        try:
            # Парсим количество монет
            data_parts = callback.data.split("_")
            count = int(data_parts[-1]) if len(data_parts) > 2 else 1

            # Получаем пользователя
            user = await db.get_or_create_user(user_id, "")
            user = ensure_user_income(user)

            # Проверяем баланс
            total_price = calculate_bronze_coin_price(user, count)

            if user['money'] >= total_price:
                # УДАЛЯЕМ ПРЕДЫДУЩЕЕ СООБЩЕНИЕ О ПОКУПКЕ (если есть)
                if user_id in BuyCoin.last_purchase_messages:
                    try:
                        await callback.bot.delete_message(
                            chat_id=user_id,
                            message_id=BuyCoin.last_purchase_messages[user_id]
                        )
                    except:
                        pass  # Если сообщение уже удалено

                # Выполняем покупку
                new_balance = user['money'] - total_price
                await db.update_user_money(user_id, new_balance)

                # Обновляем монеты
                coins = user['coins'].copy()
                coins['bronze_coin'] = coins.get('bronze_coin', 0) + count
                await db.update_user_coins(user_id, coins)
                await db.update_bronze_bought(user_id, user['bronze_coin_bought'] + count)

                # Получаем обновленные данные
                updated_user = await db.get_or_create_user(user_id, "")
                updated_user = ensure_user_income(updated_user)

                # Отправляем НОВОЕ сообщение
                response = await callback.message.answer(
                    get_buy_success_text(
                        count,
                        format_price(total_price),
                        format_price(updated_user['money']),
                        format_price(updated_user['online_income'])
                    )
                )

                # СОХРАНЯЕМ ID нового сообщения
                BuyCoin.last_purchase_messages[user_id] = response.message_id

                # ОБНОВЛЯЕМ МЕНЮ С ЦЕНАМИ
                if user_id in BuyCoin.last_shop_messages:
                    try:
                        # Обновляем текст и клавиатуру меню
                        await callback.bot.edit_message_text(
                            chat_id=user_id,
                            message_id=BuyCoin.last_shop_messages[user_id],
                            text=get_buy_menu_text(
                                format_price(updated_user['money']),
                                updated_user['bronze_coin_bought'],
                                format_price(calculate_bronze_coin_price(updated_user, 1)),
                                format_price(updated_user['online_income'])
                            ),
                            # ▼▼▼ ИЗМЕНИЛ: Добавил ID сообщения для кнопки "Обновить" ▼▼▼
                            reply_markup=get_buy_coins_keyboard(updated_user, BuyCoin.last_shop_messages[user_id])
                        )
                    except Exception as e:
                        # Если не удалось обновить (сообщение удалено и т.д.)
                        print(f"Не удалось обновить меню: {e}")

            else:
                # Обработка недостатка денег (также удаляем предыдущее сообщение)
                if user_id in BuyCoin.last_purchase_messages:
                    try:
                        await callback.bot.delete_message(
                            chat_id=user_id,
                            message_id=BuyCoin.last_purchase_messages[user_id]
                        )
                    except:
                        pass

                response = await callback.message.answer(
                    get_buy_failed_text(
                        format_price(user['money']),
                        format_price(total_price),
                        format_price(total_price - user['money'])
                    )
                )
                BuyCoin.last_purchase_messages[user_id] = response.message_id

                from datetime import datetime

                BuyCoin.last_purchase_messages[user_id] = response.message_id

            await callback.answer()

        except Exception as e:
            await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)

    # ▼▼▼ ДОБАВИЛ: Обработчик кнопки "Обновить" ▼▼▼
    @staticmethod
    @router.callback_query(lambda c: c.data.startswith("refresh_buy_menu"))
    async def handle_refresh(callback: CallbackQuery):
        """Обработчик кнопки обновления меню покупки"""
        # Удаляем предыдущее сообщение о покупке (если есть)
        user_id = callback.from_user.id
        if user_id in BuyCoin.last_purchase_messages:
            try:
                await callback.bot.delete_message(
                    chat_id=user_id,
                    message_id=BuyCoin.last_purchase_messages[user_id]
                )
            except:
                pass
            del BuyCoin.last_purchase_messages[user_id]

        # Обновляем меню покупки
        await BuyCoin.refresh_buy_menu(callback)

    # ▲▲▲ КОНЕЦ ДОБАВЛЕНИЯ ▲▲▲

    @staticmethod
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

    @staticmethod
    @router.callback_query(F.data == "back_to_menu")
    async def back_to_menu(callback: CallbackQuery):
        """Обработчик возврата в меню и удаления прошлого информационного сообщения"""
        user_id = callback.from_user.id
        if user_id in BuyCoin.last_purchase_messages:
            # Удаляем сообщение о покупке
            try:
                await callback.bot.delete_message(
                    chat_id=user_id,
                    message_id=BuyCoin.last_purchase_messages[user_id]
                )
            except:
                pass
            del BuyCoin.last_purchase_messages[user_id]
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
class Leaderboard:
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
                rating_title = "✨🏅 ТОП-10 ПО МОНЕТАМ ✨\n"
            else:
                # По умолчанию сортируем по деньгам
                sorted_users_data = sorted(
                    users_data,
                    key=lambda x: x.get('money', 0),
                    reverse=True
                )
                rating_title = "✨💰 ТОП-10 ПО ДЕНЬГАМ ✨\n"

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
                    current_user_data,
                    text=rating_title,
                    sort_by=rating_type
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
                await Leaderboard.show_leaderboard_command(callback.message, rating_type="money", user_id=callback.from_user.id)

            elif data == "leaderboard_coins":
                await callback.message.delete()  # Удаляем старое сообщение
                await Leaderboard.show_leaderboard_command(callback.message, rating_type="coins", user_id=callback.from_user.id)

            elif data == "leaderboard_back":
                await callback.message.delete()  # Удаляем старое сообщение
                await callback.message.answer(
                    "🏠 Возвращаемся в главное меню",
                    reply_markup=get_main_keyboard()
                )

            await callback.answer()
        except Exception as e:
            await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


# ========== АДМИН ПАНЕЛЬ ==========
class Admin:
    # ========== АДМИН ПАНЕЛЬ ==========

    # Временное хранилище
    admin_temp_data = {}
    broadcast_messages = {}

    @staticmethod
    @router.message(Command("admin"))
    async def admin_command(message: Message):
        """Доступ к админ-панели"""
        user_id = message.from_user.id

        try:
            from config import ADMINS
            if user_id not in ADMINS:
                return
        except ImportError:
            return

        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="📊 Список игроков", callback_data="admin_players_1"),
            InlineKeyboardButton(text="🔍 Поиск игрока", callback_data="admin_search")
        )
        builder.row(
            InlineKeyboardButton(text="📢 Отправить всем", callback_data="admin_broadcast_start"),
            InlineKeyboardButton(text="🚪 Закрыть", callback_data="admin_close")
        )

        await message.answer(
            "⚙️ АДМИН-ПАНЕЛЬ\n\nВыберите действие:",
            reply_markup=builder.as_markup()
        )

    @staticmethod
    @router.callback_query(lambda c: c.data.startswith("admin_players_"))
    async def admin_show_players(callback: CallbackQuery):
        """Показать список игроков с пагинацией"""
        user_id = callback.from_user.id

        try:
            from config import ADMINS
            if user_id not in ADMINS:
                await callback.answer("Нет доступа")
                return
        except:
            await callback.answer("Ошибка доступа")
            return

        try:
            # Получаем номер страницы
            page = int(callback.data.split("_")[2])
            users = await db.get_all_users()

            if not users:
                await callback.message.edit_text("📭 Нет зарегистрированных игроков")
                await callback.answer()
                return

            # Сортируем по деньгам
            sorted_users = sorted(users, key=lambda x: x.get('money', 0), reverse=True)
            total_players = len(users)
            total_money = sum(u.get('money', 0) for u in users)
            total_bronze = sum(u.get('bronze_coin_bought', 0) for u in users)

            # Настройки пагинации
            per_page = 10
            total_pages = (total_players + per_page - 1) // per_page
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page

            # ✅ ИСПРАВЛЕНО: Функция для определения лучшей монеты по иерархии
            def get_best_coin(coins: dict) -> tuple:
                """Возвращает (название, количество) лучшей монеты по иерархии"""
                if not coins:
                    return "Нет", 0

                # Используем иерархию из COIN_TYPES (последняя в списке - самая ценная)
                from utils.coin_config import COIN_TYPES, COIN_DISPLAY_NAMES

                # Идем от самой ценной к наименее ценной
                for coin_type in reversed(COIN_TYPES):
                    count = coins.get(coin_type, 0)
                    if count > 0:
                        coin_name = COIN_DISPLAY_NAMES.get(coin_type, coin_type)
                        return coin_name, count

                return "Нет", 0

            # Формируем текст
            text = f"📊 СТРАНИЦА {page}/{total_pages}\n"
            text += f"👥 Всего игроков: {total_players}\n"
            text += f"💰 Общая сумма: {format_price(total_money)}\n"
            text += f"🟤 Всего медных: {total_bronze:,}\n\n"
            text += "ИГРОКИ:\n"

            for i, user in enumerate(sorted_users[start_idx:end_idx], start_idx + 1):
                user_id = user.get('user_id')
                username = user.get('username', '')
                first_name = user.get('first_name', '')
                money = user.get('money', 0)
                bronze = user.get('bronze_coin_bought', 0)

                # Имя для отображения
                if username:
                    display_name = f"@{username}"
                elif first_name:
                    display_name = first_name
                else:
                    display_name = f"ID:{user_id}"

                # Лучший актив (используем исправленную функцию)
                coins = user.get('coins', {})
                best_coin, best_count = get_best_coin(coins)

                text += f"\n{i}. {display_name}\n"
                text += f"   ID: {user_id}\n"
                text += f"   Баланс: {format_price(money)}\n"
                text += f"   Медных: {bronze:,}\n"
                text += f"   Лучший актив: {best_coin} ({best_count})"

            # Создаем клавиатуру с пагинацией
            builder = InlineKeyboardBuilder()

            # Кнопки пагинации
            pagination_buttons = []
            if page > 1:
                pagination_buttons.append(
                    InlineKeyboardButton(text="⬅️ Назад", callback_data=f"admin_players_{page - 1}"))

            pagination_buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="admin_noop"))

            if page < total_pages:
                pagination_buttons.append(
                    InlineKeyboardButton(text="Вперед ➡️", callback_data=f"admin_players_{page + 1}"))

            if pagination_buttons:
                builder.row(*pagination_buttons)

            # Другие кнопки
            builder.row(
                InlineKeyboardButton(text="🔍 Поиск", callback_data="admin_search"),
                InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast_start")
            )
            builder.row(
                InlineKeyboardButton(text="🔄 Обновить", callback_data=f"admin_players_{page}"),
                InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")
            )

            await callback.message.edit_text(
                text,
                reply_markup=builder.as_markup()
            )

        except Exception as e:
            await callback.message.edit_text(f"❌ Ошибка: {str(e)}")

        await callback.answer()

    @staticmethod
    @router.callback_query(F.data == "admin_search")
    async def admin_search_start(callback: CallbackQuery):
        """Начать поиск игрока"""
        user_id = callback.from_user.id

        try:
            from config import ADMINS
            if user_id not in ADMINS:
                await callback.answer("Нет доступа")
                return
        except:
            await callback.answer("Ошибка доступа")
            return

        # Сохраняем состояние поиска
        if user_id not in Admin.admin_temp_data:
            Admin.admin_temp_data[user_id] = {}
        Admin.admin_temp_data[user_id]['search_state'] = 'waiting'

        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_back"))

        await callback.message.edit_text(
            "🔍 ПОИСК ИГРОКА\n\n"
            "Отправьте:\n"
            "• ID игрока (только цифры)\n"
            "• Имя пользователя (без @)\n"
            "• Имя (first name)\n\n"
            "Для отмены нажмите кнопку ниже:",
            reply_markup=builder.as_markup()
        )
        await callback.answer()

    @staticmethod
    async def admin_search_handler(message: Message):
        """Обработка поискового запроса"""
        user_id = message.from_user.id

        if user_id not in Admin.admin_temp_data:
            return

        if Admin.admin_temp_data[user_id].get('search_state') != 'waiting':
            return

        search_query = message.text.strip()

        try:
            from config import ADMINS
            if user_id not in ADMINS:
                return
        except:
            return

        try:
            # Получаем всех пользователей
            users = await db.get_all_users()

            # Ищем совпадения
            results = []
            for user in users:
                user_id_str = str(user.get('user_id', ''))
                username = user.get('username', '').lower()
                first_name = user.get('first_name', '').lower()

                # Проверяем все варианты
                if (search_query == user_id_str or
                        search_query.lower() == username or
                        search_query.lower() == first_name or
                        search_query.lower() in username or
                        search_query.lower() in first_name):
                    results.append(user)

            # Очищаем состояние поиска
            Admin.admin_temp_data[user_id]['search_state'] = None

            if not results:
                builder = InlineKeyboardBuilder()
                builder.row(InlineKeyboardButton(text="🔄 Новый поиск", callback_data="admin_search"))
                builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back"))

                await message.answer(
                    f"🔍 По запросу '{search_query}' ничего не найдено.\n\n"
                    "Попробуйте другой запрос:",
                    reply_markup=builder.as_markup()
                )
                return

            # Формируем результаты
            text = f"🔍 РЕЗУЛЬТАТЫ ПОИСКА: '{search_query}'\n"
            text += f"📊 Найдено: {len(results)} игроков\n\n"

            for i, user in enumerate(results[:10], 1):
                user_id = user.get('user_id')
                username = user.get('username', '')
                first_name = user.get('first_name', '')
                money = user.get('money', 0)
                bronze = user.get('bronze_coin_bought', 0)

                if username:
                    display_name = f"@{username}"
                elif first_name:
                    display_name = first_name
                else:
                    display_name = f"ID:{user_id}"

                text += f"{i}. {display_name}\n"
                text += f"   ID: {user_id}\n"
                text += f"   Баланс: {format_price(money)}\n"
                text += f"   Медных: {bronze:,}\n\n"

            if len(results) > 10:
                text += f"⚠️ Показано 10 из {len(results)} результатов\n"

            builder = InlineKeyboardBuilder()
            builder.row(
                InlineKeyboardButton(text="🔄 Новый поиск", callback_data="admin_search"),
                InlineKeyboardButton(text="📊 Список всех", callback_data="admin_players_1")
            )
            builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back"))

            await message.answer(text, reply_markup=builder.as_markup())

        except Exception as e:
            await message.answer(f"❌ Ошибка поиска: {str(e)}")

    @staticmethod
    @router.callback_query(F.data == "admin_broadcast_start")
    async def admin_broadcast_start(callback: CallbackQuery):
        """Начать рассылку"""
        user_id = callback.from_user.id

        try:
            from config import ADMINS
            if user_id not in ADMINS:
                await callback.answer("Нет доступа")
                return
        except:
            await callback.answer("Ошибка доступа")
            return

        # Сохраняем состояние рассылки
        if user_id not in Admin.broadcast_messages:
            Admin.broadcast_messages[user_id] = {}
        Admin.broadcast_messages[user_id]['state'] = 'waiting'

        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_back"))

        await callback.message.edit_text(
            "📢 РАССЫЛКА СООБЩЕНИЙ\n\n"
            "Отправьте текст сообщения для рассылки.\n"
            "Оно будет отправлено ВСЕМ игрокам.\n\n"
            "Для отмены нажмите кнопку ниже:",
            reply_markup=builder.as_markup()
        )
        await callback.answer()

    @staticmethod
    async def admin_broadcast_message_handler(message: Message):
        """Обработка текста рассылки"""
        user_id = message.from_user.id

        if user_id not in Admin.broadcast_messages:
            return

        if Admin.broadcast_messages[user_id].get('state') != 'waiting':
            return

        try:
            from config import ADMINS
            if user_id not in ADMINS:
                return
        except:
            return

        # Сохраняем сообщение и запрашиваем подтверждение
        Admin.broadcast_messages[user_id]['message'] = message.text
        Admin.broadcast_messages[user_id]['state'] = 'confirming'

        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="✅ Да, отправить", callback_data="admin_broadcast_confirm"),
            InlineKeyboardButton(text="❌ Нет, отменить", callback_data="admin_broadcast_cancel")
        )

        await message.answer(
            f"📢 ПОДТВЕРЖДЕНИЕ РАССЫЛКИ\n\n"
            f"Сообщение:\n{message.text}\n\n"
            f"Отправить это сообщение всем игрокам?",
            reply_markup=builder.as_markup()
        )

    @staticmethod
    @router.callback_query(F.data == "admin_broadcast_confirm")
    async def admin_broadcast_confirm(callback: CallbackQuery):
        """Подтверждение и отправка рассылки"""
        user_id = callback.from_user.id

        try:
            from config import ADMINS
            if user_id not in ADMINS:
                await callback.answer("Нет доступа")
                return
        except:
            await callback.answer("Ошибка доступа")
            return

        if user_id not in Admin.broadcast_messages:
            await callback.message.edit_text("❌ Нет сохраненного сообщения")
            await callback.answer()
            return

        message_text = Admin.broadcast_messages[user_id].get('message', '')
        if not message_text:
            await callback.message.edit_text("❌ Текст сообщения пуст")
            await callback.answer()
            return

        await callback.message.edit_text("🔄 Начинаю рассылку...")

        try:
            users = await db.get_all_users()
            total = len(users)
            success = 0
            failed = 0
            import asyncio
            # Отправляем всем
            for user in users:
                try:
                    target_id = user.get('user_id')
                    await callback.bot.send_message(
                        chat_id=target_id,
                        text=f"📢 СООБЩЕНИЕ ОТ АДМИНИСТРАТОРА:\n\n{message_text}"
                    )
                    success += 1
                    await asyncio.sleep(0.05)  # Задержка чтобы не превысить лимиты
                except:
                    failed += 1

            # Удаляем временные данные
            if user_id in Admin.broadcast_messages:
                del Admin.broadcast_messages[user_id]

            await callback.message.edit_text(
                f"✅ РАССЫЛКА ЗАВЕРШЕНА\n\n"
                f"📊 Статистика:\n"
                f"• Всего игроков: {total}\n"
                f"• Успешно: {success}\n"
                f"• Не отправлено: {failed}\n\n"
                f"Сообщение удалено из памяти."
            )

        except Exception as e:
            await callback.message.edit_text(f"❌ Ошибка рассылки: {str(e)}")

        await callback.answer()

    @staticmethod
    @router.callback_query(F.data == "admin_broadcast_cancel")
    async def admin_broadcast_cancel(callback: CallbackQuery):
        """Отмена рассылки"""
        user_id = callback.from_user.id

        if user_id in Admin.broadcast_messages:
            del Admin.broadcast_messages[user_id]

        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="📢 Новая рассылка", callback_data="admin_broadcast_start"))
        builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back"))

        await callback.message.edit_text(
            "❌ РАССЫЛКА ОТМЕНЕНА\n\n"
            "Сообщение удалено из памяти.",
            reply_markup=builder.as_markup()
        )
        await callback.answer()

    @staticmethod
    @router.callback_query(F.data == "admin_back")
    async def admin_back(callback: CallbackQuery):
        """Возврат в админ-панель"""
        user_id = callback.from_user.id

        try:
            from config import ADMINS
            if user_id not in ADMINS:
                await callback.answer("Нет доступа")
                return
        except:
            await callback.answer("Ошибка доступа")
            return

        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="📊 Список игроков", callback_data="admin_players_1"),
            InlineKeyboardButton(text="🔍 Поиск игрока", callback_data="admin_search")
        )
        builder.row(
            InlineKeyboardButton(text="📢 Отправить всем", callback_data="admin_broadcast_start"),
            InlineKeyboardButton(text="🚪 Закрыть", callback_data="admin_close")
        )

        await callback.message.edit_text(
            "⚙️ АДМИН-ПАНЕЛЬ\n\nВыберите действие:",
            reply_markup=builder.as_markup()
        )
        await callback.answer()

    @staticmethod
    @router.callback_query(F.data == "admin_close")
    async def admin_close(callback: CallbackQuery):
        """Закрыть админ-панель"""
        user_id = callback.from_user.id

        # Очищаем все временные данные
        if user_id in Admin.admin_temp_data:
            del Admin.admin_temp_data[user_id]
        if user_id in Admin.broadcast_messages:
            del Admin.broadcast_messages[user_id]

        await callback.message.delete()
        await callback.answer("Админ-панель закрыта")

    @router.callback_query(F.data == "admin_noop")
    async def admin_noop(callback: CallbackQuery):
        """Пустой callback для кнопок-заглушек"""
        await callback.answer()

    @staticmethod
    @router.message(Command("cancel"))
    async def cancel_operation(message: Message):
        """Отмена текущей операции админа"""
        user_id = message.from_user.id

        if user_id in Admin.admin_temp_data:
            del Admin.admin_temp_data[user_id]

        if user_id in Admin.broadcast_messages:
            del Admin.broadcast_messages[user_id]

        await message.answer("✅ Текущая операция отменена")

    @staticmethod
    async def process_search_query(message: Message):
        """Обработка поискового запроса"""
        user_id = message.from_user.id
        search_query = message.text.strip()

        # Весь код из старого admin_search_handler, но БЕЗ @router.message
        try:
            users = await db.get_all_users()
            # ... остальной код поиска

        except Exception as e:
            await message.answer(f"❌ Ошибка поиска: {str(e)}")

    @staticmethod
    async def process_broadcast_message(message: Message):
        """Обработка текста рассылки"""
        user_id = message.from_user.id

        # Сохраняем сообщение и запрашиваем подтверждение
        Admin.broadcast_messages[user_id]['message'] = message.text
        Admin.broadcast_messages[user_id]['state'] = 'confirming'

        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="✅ Да, отправить", callback_data="admin_broadcast_confirm"),
            InlineKeyboardButton(text="❌ Нет, отменить", callback_data="admin_broadcast_cancel")
        )

        await message.answer(
            f"📢 ПОДТВЕРЖДЕНИЕ РАССЫЛКИ\n\n"
            f"Сообщение:\n{message.text}\n\n"
            f"Отправить это сообщение всем игрокам?",
            reply_markup=builder.as_markup()
        )


# ========== ОБРАБОТКА ВСЕХ ОСТАЛЬНЫХ СООБЩЕНИЙ ==========
@router.message()
async def handle_all_messages(message: Message):
    """Обработчик всех остальных сообщений"""
    user_id = message.from_user.id

    # Сначала проверяем, не находится ли админ в процессе операции
    try:
        from config import ADMINS
        is_admin = user_id in ADMINS
    except ImportError:
        is_admin = False

    if is_admin:
        # Проверяем состояния админа
        if user_id in Admin.admin_temp_data and Admin.admin_temp_data[user_id].get('search_state') == 'waiting':
            # Админ в процессе поиска - обрабатываем
            await Admin.process_search_query(message)
            return

        if user_id in Admin.broadcast_messages and Admin.broadcast_messages[user_id].get('state') == 'waiting':
            # Админ в процессе рассылки - обрабатываем
            await Admin.process_broadcast_message(message)
            return

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
        "💼 Профиль", "🛒 Купить медные монеты", "🔄 Обменять монеты",
        "🏆 Таблица игроков", "❓ Помощь", "Справка по боту",
        "Команды", "Советы", "Активы в игре", "↩️ Назад в меню"
    ]

    if message.text not in processed_commands:
        if not message.text.startswith('/'):
            await message.answer(get_default_message_text())



print("✅ handlers/main_handlers.py загружен успешно")