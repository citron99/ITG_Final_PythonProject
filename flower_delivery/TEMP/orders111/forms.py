from .models import Order, Flower
from django import forms
class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['quantity', 'flower', 'address', 'delivery_time', 'delivery_date']  # Указываем названия полей из models.py
        labels = {
            'quantity': 'Количество',
            'flower': 'Букет',
            'address': 'Адрес',
            'delivery_time': 'Время доставки',
            'delivery_date': 'Дата доставки'
        }

        flower = forms.ModelChoiceField(queryset=Flower.objects.all(), empty_label="Выберите букет")

        class ReviewForm(forms.Form):
            rating = forms.ChoiceField(choices=[(i, i) for i in range(1, 6)], widget=forms.RadioSelect, label="Рейтинг")
            comment = forms.CharField(widget=forms.Textarea, label="Комментарий", required=False)