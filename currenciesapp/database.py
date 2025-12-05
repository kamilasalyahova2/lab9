import sqlite3
from typing import List, Dict, Any
from contextlib import contextmanager


class Database:
    """Класс для работы с SQLite базой данных"""

    def __init__(self, db_path: str = ':memory:'):
        self.db_path = db_path
        self.conn = None
        self._connect()
        self._create_tables()
        self._seed_data()

    def _connect(self):
        """Установка соединения с базой данных"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Для доступа к колонкам по имени

    @contextmanager
    def get_cursor(self):
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
        with self.get_cursor() as cursor:
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

    def _seed_data(self):
        """Начальное заполнение базы данных"""
        with self.get_cursor() as cursor:
            # Проверяем, есть ли уже данные
            cursor.execute("SELECT COUNT(*) FROM user")
            if cursor.fetchone()[0] == 0:
                # Добавляем пользователей
                users = [
                    ("Leisan",),
                    ("Rashit",)
                ]
                cursor.executemany("INSERT INTO user(name) VALUES(?)", users)

                # Добавляем валюты (примерные данные)
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

                # Добавляем подписки пользователей
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