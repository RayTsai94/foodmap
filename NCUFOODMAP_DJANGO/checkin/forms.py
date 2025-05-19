from django import forms
from .models import Checkin

class CheckinForm(forms.ModelForm):
    class Meta:
        model = Checkin
        fields = ['date', 'restaurant_name', 'item', 'price', 'rating', 'mood', 'comment', 'photo']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'restaurant_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '餐廳名稱'}),
            'item': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '品項'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '價格'}),
            'rating': forms.Select(attrs={'class': 'form-select'}, choices=[(i, i) for i in range(1, 6)]),
            'mood': forms.Select(attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'placeholder': '今天吃得怎麼樣呢？', 'rows': 3}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        } 