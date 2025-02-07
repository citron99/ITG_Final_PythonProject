from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from orders import views

urlpatterns = [
    path('', views.index, name='index'),
    path('add_to_cart/<int:flower_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='cart'),
    path('remove_from_cart/<int:cart_item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/confirm/', views.confirm_order, name='confirm_order'),
    path('payment_window/<int:order_id>/', views.payment_window, name='payment_window'),
    path('report/', views.generate_report, name='generate_report'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('flower/<int:flower_id>/', views.flower_detail, name='flower_detail')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)