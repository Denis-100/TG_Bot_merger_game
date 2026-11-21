def get_profile_text(user_data: dict, next_price: str, coins_list: list) -> str:
    from utils.formatters import format_price

    text = (
        f"👤 Профиль: {user_data['username']}\n"
        f"💰 Баланс: {format_price(user_data['money'])}\n"
        f"📈 Общий доход: {format_price(user_data['online_income'])} в секунду\n"
        f"💵 Куплено медных монет: {user_data.get('bronze_coin_bought', 0)}\n"
    )

    if coins_list:
        text += f"\n📦 Ваши активы:\n" + "\n".join(coins_list)

    if user_data['bronze_coin_bought'] == 0:
        text += "\n🎁 Первая медная монета: БЕСПЛАТНО (нажми '🛒 Купить медные монеты')"
    else:
        # next_price уже отформатирован, не нужно вызывать format_price снова
        text += f"\n🎯 Цена следующей медной монеты: {next_price}"

    return text