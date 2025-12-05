
from typing import List, Dict, Any, Optional
from models.currency import Currency


class CurrencyController:
    """Контроллер для бизнес-логики валют"""
    
    def __init__(self, db_controller):
        self.db = db_controller
    
    def list_currencies(self) -> List[Currency]:
        """Получение списка всех валют"""
        currencies_data = self.db.read_currencies()
        return [Currency.from_dict(data) for data in currencies_data]
    
    def get_currency(self, currency_id: int) -> Optional[Currency]:
        """Получение валюты по ID"""
        currencies_data = self.db.read_currencies()
        for data in currencies_data:
            if data['id'] == currency_id:
                return Currency.from_dict(data)
        return None
    
    def create_currency(self, currency_data: Dict[str, Any]) -> Currency:
        """Создание новой валюты"""
        # Создаем объект Currency для валидации
        currency = Currency(
            num_code=currency_data['num_code'],
            char_code=currency_data['char_code'],
            name=currency_data['name'],
            value=currency_data['value'],
            nominal=currency_data['nominal']
        )
        
        # Сохраняем в БД
        currency_id = self.db.create_currency(currency.to_dict())
        currency.id = str(currency_id)
        
        return currency
    
    def update_currency_value(self, currency_id: int, value: float) -> bool:
        """Обновление курса валюты"""
        return self.db.update_currency_value(currency_id, value)
    
    def update_currency(self, currency_id: int, currency_data: Dict[str, Any]) -> bool:
        """Полное обновление валюты"""
        return self.db.update_currency(currency_id, currency_data)
    
    def delete_currency(self, currency_id: int) -> bool:
        """Удаление валюты"""
        return self.db.delete_currency(currency_id)
    
    def get_currency_by_char_code(self, char_code: str) -> Optional[Currency]:
        """Получение валюты по символьному коду"""
        currencies_data = self.db.read_currencies(char_code)
        if currencies_data:
            return Currency.from_dict(currencies_data[0])
        return None