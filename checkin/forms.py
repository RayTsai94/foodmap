from django import forms
from .models import Checkin

class CheckinForm(forms.ModelForm):
    class Meta:
        model = Checkin
        fields = ['restaurant', 'rating', 'comment', 'image']
        widgets = {
            'restaurant': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '餐廳名稱'}),
            'rating': forms.Select(choices=[(i, f"{i} ⭐") for i in range(1, 6)], attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': '今天吃得怎麼樣呢？'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-file'}),
        }
