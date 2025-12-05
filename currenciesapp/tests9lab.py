import unittest
from unittest.mock import MagicMock, patch
from controllers.currencycontr import CurrencyController
from controllers.usercontr import UserController


class TestCurrencyController(unittest.TestCase):

    def setUp(self):
        self.mock_db = MagicMock()
        self.controller = CurrencyController(self.mock_db)

    def test_list_currencies(self):
        # Подготовка тестовых данных
        test_data = [
            {'id': 1, 'num_code': '840', 'char_code': 'USD', 'name': 'Доллар США', 'value': 90.5, 'nominal': 1}
        ]
        self.mock_db.read_currencies.return_value = test_data

        # Выполнение теста
        result = self.controller.list_currencies()

        # Проверки
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].char_code, 'USD')
        self.assertEqual(result[0].value, 90.5)
        self.mock_db.read_currencies.assert_called_once()

    def test_create_currency(self):
        # Подготовка тестовых данных
        currency_data = {
            'num_code': '840',
            'char_code': 'USD',
            'name': 'Доллар США',
            'value': 90.5,
            'nominal': 1
        }
        self.mock_db.create_currency.return_value = 1

        # Выполнение теста
        result = self.controller.create_currency(currency_data)

        # Проверки
        self.assertEqual(result.char_code, 'USD')
        self.assertEqual(result.value, 90.5)
        self.mock_db.create_currency.assert_called_once()

    def test_update_currency_value(self):
        # Подготовка тестовых данных
        self.mock_db.update_currency_value.return_value = True

        # Выполнение теста
        result = self.controller.update_currency_value(1, 95.0)

        # Проверки
        self.assertTrue(result)
        self.mock_db.update_currency_value.assert_called_once_with(1, 95.0)

    def test_delete_currency(self):
        # Подготовка тестовых данных
        self.mock_db.delete_currency.return_value = True

        # Выполнение теста
        result = self.controller.delete_currency(1)

        # Проверки
        self.assertTrue(result)
        self.mock_db.delete_currency.assert_called_once_with(1)


class TestUserController(unittest.TestCase):

    def setUp(self):
        self.mock_db = MagicMock()
        self.controller = UserController(self.mock_db)

    def test_list_users(self):
        # Подготовка тестовых данных
        test_data = [
            {'id': 1, 'name': 'Leisan'},
            {'id': 2, 'name': 'Rashit'}
        ]
        self.mock_db.read_users.return_value = test_data

        # Выполнение теста
        result = self.controller.list_users()

        # Проверки
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].name, 'Leisan')
        self.assertEqual(result[1].name, 'Rashit')
        self.mock_db.read_users.assert_called_once()

    def test_get_user_subscriptions(self):
        # Подготовка тестовых данных
        test_data = [
            {'id': 1, 'num_code': '840', 'char_code': 'USD', 'name': 'Доллар США', 'value': 90.5, 'nominal': 1}
        ]
        self.mock_db.get_user_subscriptions.return_value = test_data

        # Выполнение теста
        result = self.controller.get_user_subscriptions(1)

        # Проверки
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].char_code, 'USD')
        self.mock_db.get_user_subscriptions.assert_called_once_with(1)


if __name__ == '__main__':
    unittest.main()