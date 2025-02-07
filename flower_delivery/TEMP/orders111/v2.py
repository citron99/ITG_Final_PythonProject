import logging
from django.shortcuts import render, get_object_or_404, redirect
from .models import Flower, Order, Cart, CartItem
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

# Настроим логирование
logger = logging.getLogger(__name__)

@login_required(login_url='/accounts/login/')
def index(request):
    """Главная страница с каталогом товаров"""
    flowers = Flower.objects.all()  # Получаем все товары из модели Flower

    # Получаем или создаем корзину для пользователя
    cart, created = Cart.objects.get_or_create(user=request.user)

    # Рассчитываем количество товаров и общую стоимость в корзине
    total_items = cart.total_items()  # Общее количество товаров
    total_price = cart.total_price()  # Общая стоимость корзины

    logger.info(f"User {request.user} accessed the index page. Cart total items: {total_items}, total price: {total_price}")

    # Передаем данные в шаблон
    return render(request, 'orders/index.html', {
        'flowers': flowers,  # Передаем цветы в шаблон
        'total_items': total_items,
        'total_price': total_price
    })

@login_required(login_url='/accounts/login/')
def confirm_order(request):
    """Подтверждение заказа для всех элементов корзины"""
    cart = get_object_or_404(Cart, user=request.user)

    # Проверка, если заказ для этой корзины уже существует
    if Order.objects.filter(cart=cart).exists():
        logger.warning(f"User {request.user} tried to confirm an order for cart {cart.id}, but an order already exists.")
        return render(request, 'orders/confirm_order.html', {
            'cart': cart,
            'error': 'Вы уже оформили заказ для этой корзины.'
        })

    if request.method == 'POST':
        # Получаем данные из формы
        delivery_date = request.POST.get('delivery_date')
        delivery_time = request.POST.get('delivery_time')
        address = request.POST.get('address')

        # Проверка на заполнение всех полей
        if not delivery_date or not delivery_time or not address:
            logger.warning(f"User {request.user} failed to confirm order: Missing fields.")
            return render(request, 'orders/confirm_order.html', {
                'cart': cart, 'error': 'Все поля должны быть заполнены.'
            })

        # Создаём заказ на основе элементов корзины
        order = Order.objects.create(
            user=request.user,
            cart=cart,
            delivery_date=delivery_date,
            delivery_time=delivery_time,
            address=address
        )

        # Отправляем информацию о заказе в Telegram
        order.send_to_telegram()  # Теперь это синхронная операция

        logger.info(f"User {request.user} confirmed order {order.id}.")

        # Логирование перед редиректом
        logger.info(f"Redirecting user {request.user} to payment window for order {order.id}")

        # После подтверждения заказа корзина должна быть очищена, но только после оплаты
        return redirect('payment_window', order_id=order.id)  # Перенаправляем на окно оплаты

    return render(request, 'orders/confirm_order.html', {'cart': cart})

@login_required(login_url='/accounts/login/')
def add_to_cart(request, flower_id):
    """Добавление товара в корзину"""
    flower = get_object_or_404(Flower, id=flower_id)  # Получаем цветок по ID
    cart, created = Cart.objects.get_or_create(user=request.user)

    # Получаем или создаем элемент корзины для выбранного товара
    cart_item, created = CartItem.objects.get_or_create(cart=cart, flower=flower)
    if not created:
        # Если товар уже есть в корзине, увеличиваем его количество
        cart_item.quantity += 1
    cart_item.save()

    logger.info(f"User {request.user} added flower {flower.name} to their cart.")

    # Перенаправляем пользователя в корзину
    return redirect('cart')

@login_required(login_url='/accounts/login/')
def view_cart(request):
    """Просмотр корзины"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)  # Получаем все товары в корзине

    total_price = cart.total_price()  # Рассчитываем общую стоимость
    total_items = cart.total_items()  # Рассчитываем общее количество товаров

    logger.info(f"User {request.user} viewed their cart. Total items: {total_items}, total price: {total_price}")

    # Передаем информацию в шаблон
    return render(request, 'orders/cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'total_items': total_items
    })

@login_required(login_url='/accounts/login/')
def payment_window(request, order_id):
    """Окно оплаты"""
    order = get_object_or_404(Order, id=order_id)

    logger.info(f"User {request.user} is viewing payment window for order {order.id}.")

    # Здесь может быть интеграция с платежной системой.
    # Для простоты моделируем окно оплаты:
    if request.method == 'POST':
        payment_successful = True  # Пример: если оплата прошла успешно

        if payment_successful:
            # Очистка корзины после успешной оплаты
            order.cart.delete()  # Удаляем корзину
            logger.info(f"Payment for order {order.id} was successful. Cart {order.cart.id} deleted.")
            return redirect('index')  # Перенаправляем на главную страницу
        else:
            logger.warning(f"Payment for order {order.id} failed.")
            # Если оплата не прошла
            return render(request, 'orders/payment_window.html', {'order': order, 'error': 'Оплата не прошла.'})

    return render(request, 'orders/payment_window.html', {'order': order})

@login_required(login_url='/accounts/login/')
def remove_from_cart(request, cart_item_id):
    """Удаление элемента из корзины"""
    cart_item = get_object_or_404(CartItem, id=cart_item_id)
    cart_item.delete()

    logger.info(f"User {request.user} removed item with ID {cart_item.id} from their cart.")

    return redirect('cart')

@login_required(login_url='/accounts/login/')
def order(request, flower_id):
    """Оформление заказа для конкретного товара"""
    flower = get_object_or_404(Flower, id=flower_id)  # Получаем информацию о цветке
    if request.method == 'POST':
        delivery_date = request.POST.get('delivery_date')
        delivery_time = request.POST.get('delivery_time')
        address = request.POST.get('address')

        # Проверка на заполнение всех полей
        if not delivery_date or not delivery_time or not address:
            return render(request, 'orders/order.html', {'flower': flower, 'error': 'Все поля должны быть заполнены.'})

        # Создаем заказ на основе выбранного товара
        Order.objects.create(
            user=request.user,
            cart=None,  # Заказ без корзины, только для одного товара
            delivery_date=delivery_date,
            delivery_time=delivery_time,
            address=address
        )
        return redirect('index')  # Перенаправляем на главную страницу
    return render(request, 'orders/order.html', {'flower': flower})

def signup(request):
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})
