from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orders'

class MyAppConfig(AppConfig):
    name = 'orders'  # Укажите имя вашего приложения

    def ready(self):
        import myapp.signals  # Подключаем сигналы