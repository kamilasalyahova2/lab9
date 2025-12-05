# controllers/usercontroller.py
from typing import List, Dict, Optional
from models.user import User
from models.currency import Currency


class UserController:
    """Контроллер для бизнес-логики пользователей"""

    def __init__(self, db_controller):
        self.db = db_controller

    def list_users(self) -> List[User]:
        """Получение списка всех пользователей"""
        users_data = self.db.read_users()
        return [User(str(data['id']), data['name']) for data in users_data]

    def get_user(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID"""
        user_data = self.db.read_user(user_id)
        if user_data:
            return User(str(user_data['id']), user_data['name'])
        return None

    def get_user_subscriptions(self, user_id: int) -> List[Currency]:
        """Получение подписок пользователя"""
        subscriptions_data = self.db.get_user_subscriptions(user_id)
        return [Currency.from_dict(data) for data in subscriptions_data]

    def add_user_subscription(self, user_id: int, currency_id: int) -> int:
        """Добавление подписки пользователя на валюту"""
        return self.db.add_user_subscription(user_id, currency_id)

    def create_user(self, name: str) -> User:
        """Создание нового пользователя"""
        user_id = self.db.create_user(name)
        return User(str(user_id), name)