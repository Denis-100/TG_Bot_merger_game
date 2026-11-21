# database/sqlite_manager.py
import aiosqlite
import logging
from typing import Dict, List, Any, Optional
from utils.coin_config import get_all_coin_types

logger = logging.getLogger(__name__)


class SQLiteDatabase:
    def __init__(self, db_path: str = "users.db"):
        self.db_path = db_path
        self.conn: Optional[aiosqlite.Connection] = None

    async def connect(self):
        """Подключение к SQLite базе"""
        self.conn = await aiosqlite.connect(self.db_path)
        self.conn.row_factory = aiosqlite.Row
        await self.create_tables()
        logger.info("✅ Подключение к SQLite установлено")

    async def create_tables(self):
        """Создание таблиц в SQLite"""
        async with self.conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                money REAL DEFAULT 0,
                bronze_coin_bought INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''):
            pass

        async with self.conn.execute('''
            CREATE TABLE IF NOT EXISTS user_coins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                coin_type TEXT,
                count INTEGER DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                UNIQUE(user_id, coin_type)
            )
        '''):
            pass

        # Создаем индексы
        await self.conn.execute('CREATE INDEX IF NOT EXISTS idx_user_coins_user_id ON user_coins(user_id)')
        await self.conn.execute('CREATE INDEX IF NOT EXISTS idx_user_coins_type ON user_coins(coin_type)')

        await self.conn.commit()

    async def get_or_create_user(self, user_id: int, username: str) -> Dict[str, Any]:
        """Получение или создание пользователя"""
        # Проверяем существование пользователя
        cursor = await self.conn.execute(
            'SELECT * FROM users WHERE user_id = ?',
            (user_id,)
        )
        user = await cursor.fetchone()

        if not user:
            # Создаем нового пользователя
            await self.conn.execute('''
                INSERT INTO users (user_id, username, first_name, money, bronze_coin_bought)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, '', 0, 0))

            # Создаем записи для всех типов монет
            for coin_type in get_all_coin_types():
                await self.conn.execute('''
                    INSERT OR IGNORE INTO user_coins (user_id, coin_type, count)
                    VALUES (?, ?, ?)
                ''', (user_id, coin_type, 0))

            await self.conn.commit()

            # Получаем созданного пользователя
            cursor = await self.conn.execute(
                'SELECT * FROM users WHERE user_id = ?',
                (user_id,)
            )
            user = await cursor.fetchone()

        # Получаем монеты пользователя
        cursor = await self.conn.execute(
            'SELECT coin_type, count FROM user_coins WHERE user_id = ?',
            (user_id,)
        )
        coins_records = await cursor.fetchall()

        coins = {record['coin_type']: record['count'] for record in coins_records}

        # Рассчитываем онлайн доход
        from utils.calculations import calculate_online_income
        user_dict = {
            'user_id': user['user_id'],
            'username': user['username'],
            'first_name': user['first_name'] or '',
            'money': float(user['money']),
            'bronze_coin_bought': user['bronze_coin_bought'],
            'coins': coins,
            'online_income': calculate_online_income({'coins': coins})  # ДОБАВИТЬ ЭТО!
        }

        return user_dict

    async def update_user(self, user_id: int, data: Dict[str, Any]) -> None:
        """Обновление данных пользователя"""
        # Обновляем основную информацию
        await self.conn.execute('''
            UPDATE users 
            SET username = COALESCE(?, username),
                first_name = COALESCE(?, first_name),
                money = COALESCE(?, money),
                bronze_coin_bought = COALESCE(?, bronze_coin_bought),
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (
            data.get('username'),
            data.get('first_name'),
            data.get('money'),
            data.get('bronze_coin_bought'),
            user_id
        ))

        # Обновляем монеты
        if 'coins' in data:
            for coin_type, count in data['coins'].items():
                await self.conn.execute('''
                    INSERT INTO user_coins (user_id, coin_type, count)
                    VALUES (?, ?, ?)
                    ON CONFLICT(user_id, coin_type) 
                    DO UPDATE SET count = ?
                ''', (user_id, coin_type, count, count))

        await self.conn.commit()

    async def update_user_coins(self, user_id: int, coins: Dict[str, int]) -> None:
        """Обновление только монет пользователя"""
        for coin_type, count in coins.items():
            await self.conn.execute('''
                INSERT INTO user_coins (user_id, coin_type, count)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, coin_type) 
                DO UPDATE SET count = ?
            ''', (user_id, coin_type, count, count))

        await self.conn.commit()

    async def update_user_money(self, user_id: int, money: float) -> None:
        """Обновление только денег пользователя"""
        await self.conn.execute(
            'UPDATE users SET money = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?',
            (money, user_id)
        )
        await self.conn.commit()

    async def update_bronze_bought(self, user_id: int, count: int) -> None:
        """Обновление количества купленных медных монет"""
        await self.conn.execute(
            'UPDATE users SET bronze_coin_bought = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?',
            (count, user_id)
        )
        await self.conn.commit()

    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Получение всех пользователей"""
        cursor = await self.conn.execute('SELECT * FROM users ORDER BY money DESC')
        users = await cursor.fetchall()
        result = []

        for user in users:
            cursor = await self.conn.execute(
                'SELECT coin_type, count FROM user_coins WHERE user_id = ?',
                (user['user_id'],)
            )
            coins_records = await cursor.fetchall()
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
        cursor = await self.conn.execute('''
            SELECT COUNT(*) + 1 FROM users 
            WHERE money > (SELECT money FROM users WHERE user_id = ?)
        ''', (user_id,))
        result = await cursor.fetchone()
        return result[0] if result else 1

    async def close(self):
        """Закрытие соединения"""
        if self.conn:
            await self.conn.close()


# Создаем глобальный экземпляр
db = SQLiteDatabase()