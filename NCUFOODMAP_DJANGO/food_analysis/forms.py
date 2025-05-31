from django import forms
from .models import Ingredient, PersonalFoodRecord

# class UserFoodRecordForm(forms.ModelForm):
#     class Meta:
#         model = UserFoodRecord
#         fields = ['name', 'description', 'calories', 'protein', 'carbs', 'fat', 'image']
#         widgets = {
#             'description': forms.Textarea(attrs={'rows': 3}),
#         }

class UserFoodIngredientForm(forms.ModelForm):
    ingredient = forms.ModelChoiceField(queryset=Ingredient.objects.all())
    
    class Meta:
        model = None  # UserFoodIngredient model 不存在，暫時設為 None
        fields = ['ingredient', 'amount']

# UserFoodIngredientFormSet = forms.inlineformset_factory(
#     UserFoodRecord, 
#     UserFoodIngredient,
#     form=UserFoodIngredientForm,
#     extra=1,
#     can_delete=True
# )

class FoodAnalysisForm(forms.Form):
    food_description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': '請描述您想分析的食物，例如：一碗牛肉麵加滷蛋、麥當勞大麥克套餐...'
        }),
        label='食物描述',
        help_text='請詳細描述食物內容，AI 會根據您的描述進行營養分析'
    )

class PersonalFoodRecordForm(forms.ModelForm):
    class Meta:
        model = PersonalFoodRecord
        fields = ['food_description', 'meal_type']
        widgets = {
            'food_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '請描述您吃的食物，例如：一碗牛肉麵加滷蛋、星巴克拿鐵配可頌...'
            }),
            'meal_type': forms.Select(attrs={
                'class': 'form-select'
            })
        }
        labels = {
            'food_description': '我吃了什麼',
            'meal_type': '餐次'
        }
        help_texts = {
            'food_description': '請詳細描述食物內容，AI 會自動分析營養成分'
        }

# class SaveAnalysisToRecordForm(forms.ModelForm):
#     class Meta:
#         model = UserFoodRecord
#         fields = ['name', 'image']
#         widgets = {
#             'name': forms.TextInput(attrs={'class': 'form-control'}),
#         }
#         labels = {
#             'name': '食物名稱',
#             'image': '食物圖片（可選）'
#         } 