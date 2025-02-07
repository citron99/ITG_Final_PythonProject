import logging
from django.db import models
from django.contrib.auth.models import User  # Импортируем модель User
from aiogram import Bot
from aiogram.enums import ParseMode  # Импортируем ParseMode
from django.conf import settings
from django.utils.timezone import now  # Импортируем now для текущего времени

# Настройка логгера
logger = logging.getLogger(__name__)

# Модель товара (букет)
class Flower(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100, verbose_name='Название цветка')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    image = models.ImageField(upload_to='flowers/', verbose_name='Изображение')
    description = models.TextField(verbose_name='Описание')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Цветок'
        verbose_name_plural = 'Цветы'

# Модель корзины
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    created_at = models.DateTimeField(default=now, verbose_name='Дата создания')

    def total_price(self):
        # Подсчитывает общую цену корзины
        return sum(item.total_price() for item in self.items.all())

    def total_items(self):
        # Подсчитывает общее количество товаров в корзине
        return sum(item.quantity for item in self.items.all())

    def __str__(self):
        return f"Корзина пользователя {self.user.username}"

# Модель элемента корзины
class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    flower = models.ForeignKey(Flower, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')

    def total_price(self):
        # Подсчитывает стоимость конкретного элемента в корзине
        return self.flower.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.flower.name} (Корзина: {self.cart.id})"

# Модель заказа
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    cart = models.OneToOneField(Cart, on_delete=models.CASCADE, null=True, blank=True)  # Указано null=True, blank=True
    delivery_date = models.DateField(verbose_name='Дата доставки')
    delivery_time = models.TimeField(verbose_name='Время доставки')
    address = models.CharField(max_length=255, verbose_name='Адрес доставки')
    status = models.CharField(max_length=20, choices=[
        ('pending', 'В ожидании'),
        ('confirmed', 'Подтвержден'),
        ('delivered', 'Доставлен'),
    ], default='pending')
    created_at = models.DateTimeField(default=now)

    def total_price(self):
        # Подсчитывает общую стоимость заказа, если корзина связана с заказом
        if self.cart:
            return self.cart.total_price()
        return 0

    def __str__(self):
        return f"Заказ {self.id} от {self.user.username}"

    def send_to_telegram(self):
        """
        Метод для отправки информации о заказе в Telegram.
        Этот метод теперь синхронный.
        """
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        chat_id = settings.TELEGRAM_CHAT_ID  # ID чата, куда бот отправляет сообщения

        # Получаем все элементы из корзины
        order_data = []
        for cart_item in self.cart.items.all():  # Перебираем все товары в корзине
            flower = cart_item.flower
            order_data.append({
                "flower_image": flower.image.url,  # Используем изображение из связанного букета
                "cost": cart_item.total_price(),
                "name": flower.name,
                "quantity": cart_item.quantity,
            })

        # Формируем текст сообщения
        text = "Получен новый заказ!\n\n"
        for item in order_data:
            text += f"🌸 Букет: {item['name']} x {item['quantity']}\n" \
                    f"💰 Стоимость: {item['cost']} ₽\n"
        text += f"📅 Дата доставки: {self.delivery_date}\n" \
                f"🕑 Время доставки: {self.delivery_time}\n" \
                f"📍 Адрес доставки: {self.address}\n" \
                f"💬 Комментарий: {self.comment if hasattr(self, 'comment') else 'Без комментариев'}"

        # Логируем данные перед отправкой
        logger.info(f"Sending order data to Telegram: {text}")

        try:
            # Отправляем фото с описанием заказа
            for item in order_data:
                bot.send_photo(chat_id, item["flower_image"], caption=text, parse_mode=ParseMode.MARKDOWN)
            logger.info("Order data sent successfully to Telegram.")
        except Exception as e:
            logger.error(f"Failed to send order to Telegram: {e}")
