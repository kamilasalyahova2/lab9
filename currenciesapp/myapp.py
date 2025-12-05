
from urllib.parse import urlparse, parse_qs
from jinja2 import Environment, FileSystemLoader, select_autoescape
from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import json

from models import Author, User, App
from controllers import DatabaseController, CurrencyController, UserController
from lab7 import get_currencies

# Инициализация Jinja2
current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(current_dir, 'templates')
env = Environment(
    loader=FileSystemLoader(templates_dir),
    autoescape=select_autoescape()
)

# Инициализация контроллеров
db_controller = DatabaseController(':memory:')
db_controller.seed_initial_data()
currency_controller = CurrencyController(db_controller)
user_controller = UserController(db_controller)

# Инициализация данных приложения
main_author = Author("Kamila", 'Р3124')
main_app = App("Знаю все валюты", "1.0.0", main_author)


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)

        # Устанавливаем заголовки по умолчанию
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()

        # Навигация для всех страниц
        navigation = [
            {'caption': 'Главная', 'href': '/'},
            {'caption': 'Об авторе', 'href': '/author'},
            {'caption': 'Пользователи', 'href': '/users'},
            {'caption': 'Курсы валют', 'href': '/currencies'},
            {'caption': 'Управление валютами', 'href': '/currencies/admin'}
        ]

        try:
            if parsed_path.path == '/':
                # Главная страница
                currencies = currency_controller.list_currencies()
                users = user_controller.list_users()

                template = env.get_template("index.html")
                result = template.render(
                    app_name=main_app.name,
                    myapp=main_app.name,
                    version=main_app.version,
                    navigation=navigation,
                    author_name=main_app.author.name,
                    author_group=main_author.group,
                    currencies=currencies[:2],  # Показываем только первые 2 валюты
                    users=users[:2]  # Показываем только первых 2 пользователей
                )

            elif parsed_path.path == '/author':
                # Страница об авторе
                template = env.get_template("author.html")
                result = template.render(
                    app_name=main_app.name,
                    app_version=main_app.version,
                    navigation=navigation,
                    author_name=main_author.name,
                    author_group=main_author.group
                )

            elif parsed_path.path == '/users':
                # Список пользователей
                users = user_controller.list_users()

                template = env.get_template("users.html")
                result = template.render(
                    app_name=main_app.name,
                    navigation=navigation,
                    users=users
                )

            elif parsed_path.path == '/user':
                # Страница пользователя
                user_id = query_params.get('id', [None])[0]

                if not user_id:
                    result = self._error_page("400 - Не указан ID пользователя", 400)
                else:
                    user = user_controller.get_user(int(user_id))
                    if not user:
                        result = self._error_page("404 - Пользователь не найден", 404)
                    else:
                        subscriptions = user_controller.get_user_subscriptions(int(user_id))

                        template = env.get_template("user.html")
                        result = template.render(
                            app_name=main_app.name,
                            navigation=navigation,
                            user=user,
                            subscriptions=subscriptions
                        )

            elif parsed_path.path == '/currencies':
                # Страница с курсами валют
                try:
                    # Получаем актуальные курсы
                    actual_rates = get_currencies(["USD", "EUR", "GBP", "JPY"])

                    # Обновляем курсы в БД
                    for char_code, value in actual_rates.items():
                        currency = currency_controller.get_currency_by_char_code(char_code)
                        if currency:
                            currency_controller.update_currency_value(currency.id, value)

                    currencies = currency_controller.list_currencies()

                    template = env.get_template("currencies.html")
                    result = template.render(
                        app_name=main_app.name,
                        navigation=navigation,
                        currencies=currencies,
                        success=True,
                        error=None
                    )
                except Exception as e:
                    # Если ошибка, показываем данные из БД
                    currencies = currency_controller.list_currencies()

                    template = env.get_template("currencies.html")
                    result = template.render(
                        app_name=main_app.name,
                        navigation=navigation,
                        currencies=currencies,
                        success=False,
                        error=str(e)
                    )

            elif parsed_path.path == '/currencies/admin':
                # Админка для управления валютами
                currencies = currency_controller.list_currencies()

                template = env.get_template("currencies_admin.html")
                result = template.render(
                    app_name=main_app.name,
                    navigation=navigation,
                    currencies=currencies
                )

            elif parsed_path.path == '/currency/delete':
                # Удаление валюты
                currency_id = query_params.get('id', [None])[0]

                if not currency_id:
                    result = self._error_page("400 - Не указан ID валюты", 400)
                else:
                    success = currency_controller.delete_currency(int(currency_id))
                    if success:
                        # Перенаправляем на страницу управления
                        self.send_response(303)
                        self.send_header('Location', '/currencies/admin')
                        self.end_headers()
                        return
                    else:
                        result = self._error_page("404 - Валюта не найдена", 404)

            elif parsed_path.path == '/currency/show':
                # Отладочная страница для просмотра валют
                currencies = currency_controller.list_currencies()
                result = f"<html><body><pre>{json.dumps([c.__dict__ for c in currencies], indent=2)}</pre></body></html>"

            else:
                result = self._error_page("404 - Страница не найдена", 404)

        except Exception as e:
            result = self._error_page(f"500 - Внутренняя ошибка сервера: {str(e)}", 500)

        self.wfile.write(bytes(result, "utf-8"))

    def do_POST(self):
        """Обработка POST-запросов"""
        parsed_path = urlparse(self.path)

        if parsed_path.path == '/currency/create':
            # Получаем данные формы
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            form_data = parse_qs(post_data)

            # Создаем новую валюту
            try:
                currency_data = {
                    'num_code': form_data['num_code'][0],
                    'char_code': form_data['char_code'][0].upper(),
                    'name': form_data['name'][0],
                    'value': float(form_data['value'][0]),
                    'nominal': int(form_data['nominal'][0])
                }

                currency_controller.create_currency(currency_data)

                # Перенаправляем на страницу управления
                self.send_response(303)
                self.send_header('Location', '/currencies/admin')
                self.end_headers()

            except Exception as e:
                result = self._error_page(f"400 - Ошибка при создании валюты: {str(e)}", 400)
                self.send_response(400)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(bytes(result, "utf-8"))

        else:
            result = self._error_page("404 - Страница не найдена", 404)
            self.send_response(404)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(bytes(result, "utf-8"))

    def _error_page(self, message: str, status_code: int = 500):
        """Создание страницы ошибки"""
        template = env.get_template("error.html")
        return template.render(
            app_name=main_app.name,
            navigation=[
                {'caption': 'Главная', 'href': '/'},
                {'caption': 'Об авторе', 'href': '/author'}
            ],
            error_message=message,
            status_code=status_code
        )


if __name__ == '__main__':
    httpd = HTTPServer(('localhost', 8080), SimpleHTTPRequestHandler)
    print('Server is running on http://localhost:8080')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
        db_controller.close()








