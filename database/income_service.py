# database/income_service.py
import asyncio
import logging
from database import db  # <-- ИЗМЕНИТЬ ЗДЕСЬ!
from utils.calculations import calculate_online_income

logger = logging.getLogger(__name__)


async def income_loop() -> None:
    """Асинхронный цикл начисления дохода"""
    logger.info("Запущен цикл начисления дохода")

    while True:
        try:
            # Получаем всех пользователей
            users = await db.get_all_users()

            for user in users:
                try:
                    # Рассчитываем доход пользователя
                    income = calculate_online_income(user)

                    if income > 0:
                        # Обновляем баланс
                        new_balance = user['money'] + income
                        await db.update_user_money(user['user_id'], new_balance)

                        # Логируем (опционально)
                        if new_balance >= 100_000_000 and user['money'] < 100_000_000:
                            logger.info(f"Пользователь {user['user_id']} достиг 100M+!")

                except Exception as e:
                    logger.error(f"Ошибка при начислении дохода пользователю {user['user_id']}: {e}")
                    continue

            # Ждем 1 секунду
            await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Критическая ошибка в income_loop: {e}")
            await asyncio.sleep(5)


async def award_first_coin(user_id: int) -> None:
    """Награждение первой бесплатной монетой"""
    from database import db  # <-- ИЗМЕНИТЬ ЗДЕСЬ!

    # Получаем пользователя
    user = await db.get_or_create_user(user_id, "")

    # Добавляем первую медную монету
    coins = user['coins']
    coins['bronze_coin'] = coins.get('bronze_coin', 0) + 1

    # Обновляем данные
    await db.update_user_coins(user_id, coins)
    await db.update_bronze_bought(user_id, 1)