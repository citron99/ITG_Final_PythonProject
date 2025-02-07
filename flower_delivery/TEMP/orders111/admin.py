from django.contrib import admin
from .models import Order, Flower, CartItem

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'get_flowers', 'get_total_quantity', 'delivery_date', 'status')
    list_filter = ('status', 'delivery_date', 'user')  # Фильтры по статусу, дате и пользователю

    def get_flowers(self, obj):
        if obj.cart:
            return ", ".join([f"{item.flower.name} ({item.quantity} шт.)" for item in obj.cart.items.all()])
        return "Нет товаров"

    def get_total_quantity(self, obj):
        if obj.cart:
            return sum(item.quantity for item in obj.cart.items.all())
        return 0

    get_flowers.short_description = 'Букеты'
    get_total_quantity.short_description = 'Общее количество'

admin.site.register(Flower)
admin.site.register(Order, OrderAdmin)
admin.site.register(CartItem)
