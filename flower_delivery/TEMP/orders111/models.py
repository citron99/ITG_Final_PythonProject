import logging
import os
import requests
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.timezone import now

logger = logging.getLogger(__name__)

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


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    created_at = models.DateTimeField(default=now, verbose_name='Дата создания')

    def total_price(self):
        return sum(item.total_price() for item in self.items.all())

    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    def __str__(self):
        return f"Корзина пользователя {self.user.username}"


class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    flower = models.ForeignKey(Flower, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')

    def total_price(self):
        return self.flower.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.flower.name} (Корзина: {self.cart.id})"


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    cart = models.OneToOneField(Cart, on_delete=models.CASCADE, null=True, blank=True)
    delivery_date = models.DateField(verbose_name='Дата доставки')
    delivery_time = models.TimeField(verbose_name='Время доставки')
    address = models.CharField(max_length=255, verbose_name='Адрес доставки')
    status = models.CharField(max_length=20, choices=[
        ('pending', 'В ожидании'),
        ('confirmed', 'Подтвержден'),
        ('delivered', 'Доставлен'),
    ], default='pending')
    comment = models.TextField(null=True, blank=True, verbose_name='Комментарий')
    created_at = models.DateTimeField(default=now)

    def total_price(self):
        if self.cart:
            return self.cart.total_price()
        return 0

    def __str__(self):
        return f"Заказ {self.id} от {self.user.username}"

    def send_to_telegram(self):
        chat_id = settings.TELEGRAM_CHAT_ID
        bot_token = settings.TELEGRAM_BOT_TOKEN
        url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"

        order_data = []
        for cart_item in self.cart.items.all():
            flower = cart_item.flower
            flower_image_path = os.path.join(settings.MEDIA_ROOT, flower.image.name)

            if not os.path.exists(flower_image_path):
                logger.error(f"Image file not found: {flower_image_path}")
                continue

            order_data.append({
                "flower_image": flower_image_path,
                "cost": cart_item.total_price(),
                "name": flower.name,
                "quantity": cart_item.quantity,
            })

        text = "Получен новый заказ!\n\n"
        for item in order_data:
            text += f"🌸 Букет: {item['name']} x {item['quantity']}\n" \
                    f"💰 Стоимость: {item['cost']} ₽\n"
        text += f"📅 Дата доставки: {self.delivery_date}\n" \
                f"🕑 Время доставки: {self.delivery_time}\n" \
                f"📍 Адрес доставки: {self.address}\n" \
                f"💬 Комментарий: {self.comment if self.comment else 'Без комментариев'}"

        try:
            for item in order_data:
                with open(item["flower_image"], 'rb') as photo:
                    response = requests.post(url, data={
                        "chat_id": chat_id,
                        "caption": text,
                        "parse_mode": "Markdown",
                    }, files={"photo": photo})

                if response.status_code == 200:
                    logger.info("Order data sent successfully to Telegram.")
                else:
                    logger.error(f"Failed to send order to Telegram: {response.text}")

        except Exception as e:
            logger.error(f"Error sending order to Telegram: {e}")

class Review(models.Model):
    flower = models.ForeignKey(Flower, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)], verbose_name='Рейтинг (1-5)')
    comment = models.TextField(null=True, blank=True, verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']

    def __str__(self):
        return f"Отзыв от {self.user.username} на {self.flower.name}"

class Report(models.Model):
    date = models.DateField(auto_now_add=True, verbose_name='Дата')
    total_orders = models.IntegerField(default=0, verbose_name='Общее количество заказов')
    total_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Общий объем продаж')
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Общий доход')
    total_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Общие расходы')
    profit = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Прибыль')

    def __str__(self):
        return f"Отчет за {self.date}"

    class Meta:
        verbose_name = 'Отчет'
        verbose_name_plural = 'Отчеты'
        ordering = ['-date']
