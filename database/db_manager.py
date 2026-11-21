import asyncpg
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from config import DATABASE_URL

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Установка соединения с базой данных"""
        try:
            self.pool = await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=20)
            await self.create_tables()
            logger.info("✅ Подключение к базе данных установлено")
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к базе данных: {e}")
            raise

    async def create_tables(self):
        """Создание таблиц"""
        async with self.pool.acquire() as conn:
            # Таблица пользователей
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(255),
                    first_name VARCHAR(255),
                    money DOUBLE PRECISION DEFAULT 0,
                    bronze_coin_bought INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Таблица монет пользователей
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS user_coins (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                    coin_type VARCHAR(50),
                    count INTEGER DEFAULT 0,
                    UNIQUE(user_id, coin_type)
                )
            ''')

            # Индексы для оптимизации
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_user_coins_user_id ON user_coins(user_id)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_user_coins_type ON user_coins(coin_type)')

            logger.info("✅ Таблицы созданы/проверены")

    async def get_or_create_user(self, user_id: int, username: str) -> Dict[str, Any]:
        """Получение или создание пользователя"""
        async with self.pool.acquire() as conn:
            # Проверяем существование пользователя
            user = await conn.fetchrow(
                'SELECT * FROM users WHERE user_id = $1',
                user_id
            )

            if not user:
                # Создаем нового пользователя
                await conn.execute('''
                    INSERT INTO users (user_id, username, first_name, money, bronze_coin_bought)
                    VALUES ($1, $2, $3, $4, $5)
                ''', user_id, username, '', 0, 0)

                # Создаем записи для всех типов монет
                from utils.coin_config import COIN_TYPES
                for coin_type in COIN_TYPES:
                    await conn.execute('''
                        INSERT INTO user_coins (user_id, coin_type, count)
                        VALUES ($1, $2, $3)
                        ON CONFLICT (user_id, coin_type) DO NOTHING
                    ''', user_id, coin_type, 0)

                user = await conn.fetchrow(
                    'SELECT * FROM users WHERE user_id = $1',
                    user_id
                )

            # Получаем монеты пользователя
            coins_records = await conn.fetch(
                'SELECT coin_type, count FROM user_coins WHERE user_id = $1',
                user_id
            )

            coins = {record['coin_type']: record['count'] for record in coins_records}

            return {
                'user_id': user['user_id'],
                'username': user['username'],
                'first_name': user['first_name'] or '',
                'money': float(user['money']),
                'bronze_coin_bought': user['bronze_coin_bought'],
                'coins': coins
            }

    async def update_user(self, user_id: int, data: Dict[str, Any]) -> None:
        """Обновление данных пользователя"""
        async with self.pool.acquire() as conn:
            # Обновляем основную информацию
            await conn.execute('''
                UPDATE users 
                SET username = COALESCE($2, username),
                    first_name = COALESCE($3, first_name),
                    money = COALESCE($4, money),
                    bronze_coin_bought = COALESCE($5, bronze_coin_bought),
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $1
            ''', user_id,
                               data.get('username'),
                               data.get('first_name'),
                               data.get('money'),
                               data.get('bronze_coin_bought'))

            # Обновляем монеты
            if 'coins' in data:
                for coin_type, count in data['coins'].items():
                    await conn.execute('''
                        INSERT INTO user_coins (user_id, coin_type, count)
                        VALUES ($1, $2, $3)
                        ON CONFLICT (user_id, coin_type) 
                        DO UPDATE SET count = $3
                    ''', user_id, coin_type, count)

    async def update_user_coins(self, user_id: int, coins: Dict[str, int]) -> None:
        """Обновление только монет пользователя"""
        async with self.pool.acquire() as conn:
            for coin_type, count in coins.items():
                await conn.execute('''
                    INSERT INTO user_coins (user_id, coin_type, count)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (user_id, coin_type) 
                    DO UPDATE SET count = $3
                ''', user_id, coin_type, count)

    async def update_user_money(self, user_id: int, money: float) -> None:
        """Обновление только денег пользователя"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                'UPDATE users SET money = $1, updated_at = CURRENT_TIMESTAMP WHERE user_id = $2',
                money, user_id
            )

    async def update_bronze_bought(self, user_id: int, count: int) -> None:
        """Обновление количества купленных медных монет"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                'UPDATE users SET bronze_coin_bought = $1, updated_at = CURRENT_TIMESTAMP WHERE user_id = $2',
                count, user_id
            )

    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Получение всех пользователей"""
        async with self.pool.acquire() as conn:
            users = await conn.fetch('SELECT * FROM users ORDER BY money DESC')
            result = []

            for user in users:
                coins_records = await conn.fetch(
                    'SELECT coin_type, count FROM user_coins WHERE user_id = $1',
                    user['user_id']
                )
                coins = {record['coin_type']: record['count'] for record in coins_records}

                result.append({
                    'user_id': user['user_id'],
                    'username': user['username'],
                    'first_name': user['first_name'] or '',
                    'money': float(user['money']),
                    'bronze_coin_bought': user['bronze_coin_bought'],
                    'coins': coins
                })

            return result

    async def get_user_position(self, user_id: int) -> int:
        """Получение позиции пользователя в рейтинге"""
        async with self.pool.acquire() as conn:
            position = await conn.fetchval('''
                SELECT COUNT(*) + 1 FROM users 
                WHERE money > (SELECT money FROM users WHERE user_id = $1)
            ''', user_id)
            return position

    async def close(self):
        """Закрытие соединения"""
        if self.pool:
            await self.pool.close()


# Создаем глобальный экземпляр базы данных
db = Database()