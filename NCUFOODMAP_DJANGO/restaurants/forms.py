from django import forms
from django.db.models import Count
from .models import Review, Category

class ReviewForm(forms.ModelForm):
    """用於提交餐廳評論的表單"""
    class Meta:
        model = Review
        fields = ['author', 'rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(choices=[(i, i) for i in range(1, 6)]),
            'comment': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'author': '您的名字',
            'rating': '評分',
            'comment': '評論',
        }
        help_texts = {
            'rating': '請選擇1到5顆星',
        }

class RestaurantFilterForm(forms.Form):
    """用於過濾餐廳列表的表單"""
    category = forms.ModelChoiceField(
        queryset=Category.objects.annotate(
            restaurant_count=Count('restaurants')
        ).filter(restaurant_count__gt=0),
        required=False,
        empty_label="所有分類",
        label="分類",
    )
    
    min_rating = forms.ChoiceField(
        choices=[
            ('', '所有評分'),
            ('3', '3星及以上'),
            ('4', '4星及以上'),
            ('4.5', '4.5星及以上'),
        ],
        required=False,
        label="最低評分",
    )

    name_or_address = forms.CharField(
        required=False,
        label="關鍵字搜尋",
        widget=forms.TextInput(attrs={'placeholder': '餐廳名稱或地址'})
    ) 