
import sqlite3
from contextlib import contextmanager
from typing import List, Dict, Any, Optional


class DatabaseController:
    """Контроллер для работы с базой данных"""
    
    def __init__(self, db_path: str = ':memory:'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
    
    @contextmanager
    def _get_cursor(self):
        """Контекстный менеджер для работы с курсором"""
        cursor = self.conn.cursor()
        try:
            yield cursor
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e
        finally:
            cursor.close()
    
    def _create_tables(self):
        """Создание таблиц в базе данных"""
        with self._get_cursor() as cursor:
            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL
                )
            ''')
            
            # Таблица валют
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS currency (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    num_code TEXT NOT NULL,
                    char_code TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    value FLOAT,
                    nominal INTEGER
                )
            ''')
            
            # Таблица подписок пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_currency (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    currency_id INTEGER NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES user(id) ON DELETE CASCADE,
                    FOREIGN KEY(currency_id) REFERENCES currency(id) ON DELETE CASCADE,
                    UNIQUE(user_id, currency_id)
                )
            ''')
    
    # CRUD операции для Currency
    
    def create_currency(self, currency_data: Dict[str, Any]) -> int:
        """Создание новой валюты"""
        sql = '''
            INSERT INTO currency(num_code, char_code, name, value, nominal)
            VALUES(:num_code, :char_code, :name, :value, :nominal)
        '''
        with self._get_cursor() as cursor:
            cursor.execute(sql, currency_data)
            return cursor.lastrowid
    
    def read_currencies(self, char_code: Optional[str] = None) -> List[Dict]:
        """Чтение валют"""
        if char_code:
            sql = "SELECT * FROM currency WHERE char_code = ?"
            params = (char_code,)
        else:
            sql = "SELECT * FROM currency ORDER BY char_code"
            params = ()
        
        with self._get_cursor() as cursor:
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def update_currency_value(self, currency_id: int, value: float) -> bool:
        """Обновление курса валюты"""
        sql = "UPDATE currency SET value = ? WHERE id = ?"
        with self._get_cursor() as cursor:
            cursor.execute(sql, (value, currency_id))
            return cursor.rowcount > 0
    
    def update_currency(self, currency_id: int, currency_data: Dict[str, Any]) -> bool:
        """Полное обновление валюты"""
        sql = '''
            UPDATE currency 
            SET num_code = :num_code, 
                char_code = :char_code,
                name = :name,
                value = :value,
                nominal = :nominal
            WHERE id = :id
        '''
        currency_data['id'] = currency_id
        
        with self._get_cursor() as cursor:
            cursor.execute(sql, currency_data)
            return cursor.rowcount > 0
    
    def delete_currency(self, currency_id: int) -> bool:
        """Удаление валюты"""
        sql = "DELETE FROM currency WHERE id = ?"
        with self._get_cursor() as cursor:
            cursor.execute(sql, (currency_id,))
            return cursor.rowcount > 0
    
    # CRUD операции для User
    
    def create_user(self, name: str) -> int:
        """Создание нового пользователя"""
        sql = "INSERT INTO user(name) VALUES(?)"
        with self._get_cursor() as cursor:
            cursor.execute(sql, (name,))
            return cursor.lastrowid
    
    def read_users(self) -> List[Dict]:
        """Чтение всех пользователей"""
        sql = "SELECT * FROM user"
        with self._get_cursor() as cursor:
            cursor.execute(sql)
            return [dict(row) for row in cursor.fetchall()]
    
    def read_user(self, user_id: int) -> Optional[Dict]:
        """Чтение одного пользователя"""
        sql = "SELECT * FROM user WHERE id = ?"
        with self._get_cursor() as cursor:
            cursor.execute(sql, (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # Операции для подписок
    
    def add_user_subscription(self, user_id: int, currency_id: int) -> int:
        """Добавление подписки пользователя на валюту"""
        sql = "INSERT INTO user_currency(user_id, currency_id) VALUES(?, ?)"
        with self._get_cursor() as cursor:
            cursor.execute(sql, (user_id, currency_id))
            return cursor.lastrowid
    
    def get_user_subscriptions(self, user_id: int) -> List[Dict]:
        """Получение подписок пользователя"""
        sql = '''
            SELECT c.* 
            FROM currency c
            JOIN user_currency uc ON c.id = uc.currency_id
            WHERE uc.user_id = ?
        '''
        with self._get_cursor() as cursor:
            cursor.execute(sql, (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def remove_user_subscription(self, subscription_id: int) -> bool:
        """Удаление подписки"""
        sql = "DELETE FROM user_currency WHERE id = ?"
        with self._get_cursor() as cursor:
            cursor.execute(sql, (subscription_id,))
            return cursor.rowcount > 0
    
    def seed_initial_data(self):
        """Начальное заполнение базы данных"""
        # Добавляем начальные данные, если таблицы пусты
        with self._get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM user")
            if cursor.fetchone()[0] == 0:
                # Пользователи
                users = [("Leisan",), ("Rashit",)]
                cursor.executemany("INSERT INTO user(name) VALUES(?)", users)
                
                # Валюты
                currencies = [
                    ("840", "USD", "Доллар США", 90.5, 1),
                    ("978", "EUR", "Евро", 98.2, 1),
                    ("826", "GBP", "Фунт стерлингов", 115.0, 1),
                    ("392", "JPY", "Японская иена", 0.61, 100)
                ]
                cursor.executemany(
                    "INSERT INTO currency(num_code, char_code, name, value, nominal) VALUES(?, ?, ?, ?, ?)",
                    currencies
                )
                
                # Подписки
                cursor.execute("SELECT id FROM user WHERE name = 'Leisan'")
                leisan_id = cursor.fetchone()[0]
                
                cursor.execute("SELECT id FROM user WHERE name = 'Rashit'")
                rashit_id = cursor.fetchone()[0]
                
                cursor.execute("SELECT id FROM currency WHERE char_code = 'USD'")
                usd_id = cursor.fetchone()[0]
                
                cursor.execute("SELECT id FROM currency WHERE char_code = 'EUR'")
                eur_id = cursor.fetchone()[0]
                
                cursor.execute("SELECT id FROM currency WHERE char_code = 'GBP'")
                gbp_id = cursor.fetchone()[0]
                
                subscriptions = [
                    (leisan_id, usd_id),
                    (leisan_id, eur_id),
                    (rashit_id, gbp_id)
                ]
                cursor.executemany(
                    "INSERT INTO user_currency(user_id, currency_id) VALUES(?, ?)",
                    subscriptions
                )
    
    def close(self):
        """Закрытие соединения с базой данных"""
        if self.conn:
            self.conn.close()
    
    def __del__(self):
        self.close()