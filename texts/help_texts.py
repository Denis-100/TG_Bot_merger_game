from utils.coin_config import INCOME_PER_SECOND, EXCHANGE_RATES, COIN_DISPLAY_NAMES
from utils.formatters import format_price


def get_help_main_text() -> str:
    return (
        "📖 РАЗДЕЛЫ ПОМОЩИ:\n\n"
        "Выберите раздел помощи, который вас интересует:"
    )


def get_bot_info_text() -> str:
    return (
        "🤖 СПРАВКА ПО БОТУ:\n\n"
        "Это бот для заработка и объединения монет!\n\n"
        "💰 Как работает бот:\n"
        "• Вы начинаете с 0 монет и получаете первую медную монету бесплатно\n"
        "• Каждая монета приносит доход каждую секунду\n"
        "• Объединяйте 3 одинаковые монеты, чтобы получить 1 монету следующего уровня\n"
        "💡 Основная цель - достич лучшей монеты!\n"
        "• При достижении 100M+ баланса открываются новые кнопки покупки!\n"
        "• Можно покупать сразу 100, 500, 2500 или 10000 медных монет!"
    )


def get_commands_text() -> str:
    return (
        "📋 КОМАНДЫ И КНОПКИ:\n\n"
        "Основное меню:\n"
        "• 💼 Профиль - ваш баланс и активы\n"
        "• 🛒 Купить медные монеты - покупка медных монет\n"
        "• 🔄 Обменять монеты - автоматический обмен всех монет, на монеты лучшего уровня\n"
        "• 🏆 Таблица игроков - рейтинг всех игроков\n"
        "• ❓ Помощь - эта справка\n\n"
        "Команды в чате:\n"
        "• /start - запустить бота\n"
        "• /top или /игроки - таблица лидеров\n"
        "• /help - справка\n"
    )


def get_tips_text() -> str:
    return (
        "💡 СОВЕТЫ ПО ИГРЕ:\n\n"
        "1. Покупайте медные монеты\n"
        "2. Регулярно обменивайте монеты в более ценные\n"
        "3. Возвращайтесь в игру, чтобы покупать больше медных монет\n\n"
    )


def get_assets_info_text() -> str:
    """Создает описание активов на основе конфигурации доходов"""
    text = "💰 АКТИВЫ В ИГРЕ:\n\n"
    text += "Доход указан за 1 секунду:\n\n"

    # Группируем активы по категориям для лучшего отображения
    categories = {
        "🟤 Базовые": ['bronze_coin', 'bronze_bar'],
        "⚙️ Железные": ['iron_coin', 'iron_bar'],
        "⚪ Серебряные": ['silver_coin', 'silver_bar'],
        "🟠 Бронзовые (высший сорт)": ['bronze_coin_high', 'bronze_bar_high'],
        "🟡 Золотые": ['gold_coin', 'gold_bar'],
        "💎 Драгоценные камни": ['emerald', 'sapphire', 'ruby'],
        "⚜️ Платиновые": ['platinum_coin', 'platinum_bar'],
        "💎 Алмаз": ['diamond'],
        "🔥 Эксклюзивные": ['lava_coin']
    }
    count = 1
    for category_name, coin_types in categories.items():
        text += f"{category_name}:\n"
        for coin_type in coin_types:
            display_name = COIN_DISPLAY_NAMES.get(coin_type, coin_type)
            income = INCOME_PER_SECOND.get(coin_type, 0)
            exchange_rate = EXCHANGE_RATES.get(coin_type, 0)

            if exchange_rate > 0:
                text += f"{count}. {display_name}: {format_price(income)}/сек (нужно {exchange_rate} для обмена)\n"
            else:
                text += f"{count}. {display_name}: {format_price(income)}/сек (максимальный уровень)\n"
            count += 1
        text += "\n"


    text += "📊 Обмен: 3 монеты = 1 монета следующего уровня"
    return text
