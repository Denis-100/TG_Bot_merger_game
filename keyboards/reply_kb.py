from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Основное меню
def get_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💼 Профиль"), KeyboardButton(text="🛒 Купить медные монеты")],
            [KeyboardButton(text="🔄 Обменять монеты"), KeyboardButton(text="🏆 Таблица игроков")],
            [KeyboardButton(text="❓ Помощь")]
        ],
        resize_keyboard=True
    )

# Меню помощи
def get_help_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Справка по боту"), KeyboardButton(text="Команды")],
            [KeyboardButton(text="Советы"), KeyboardButton(text="Активы в игре")],
            [KeyboardButton(text="↩️ Назад в меню")]
        ],
        resize_keyboard=True
    )