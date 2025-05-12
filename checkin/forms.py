from django import forms
from .models import Checkin

class CheckinForm(forms.ModelForm):
    class Meta:
        model = Checkin
        fields = ['date', 'restaurant', 'item', 'price', 'rating', 'emotion_tag', 'comment', 'image']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'restaurant': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '餐廳名稱'}),
            'item': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '品項'}),
            'price': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '價格'}),
            'rating': forms.Select(choices=[(i, f"{i} ⭐") for i in range(1, 6)], attrs={'class': 'form-select'}),
            'emotion_tag': forms.Select(choices=[('開心', '開心'), ('普通', '普通'), ('難過', '難過'), ('驚訝', '驚訝'), ('滿足', '滿足')], attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': '今天吃得怎麼樣呢？'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-file'}),
        }
