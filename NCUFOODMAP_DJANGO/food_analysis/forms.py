from django import forms
from .models import UserFoodRecord, Ingredient, UserFoodIngredient

class UserFoodRecordForm(forms.ModelForm):
    class Meta:
        model = UserFoodRecord
        fields = ['name', 'description', 'calories', 'protein', 'carbs', 'fat', 'image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class UserFoodIngredientForm(forms.ModelForm):
    ingredient = forms.ModelChoiceField(queryset=Ingredient.objects.all())
    
    class Meta:
        model = UserFoodIngredient
        fields = ['ingredient', 'amount']

UserFoodIngredientFormSet = forms.inlineformset_factory(
    UserFoodRecord, 
    UserFoodIngredient,
    form=UserFoodIngredientForm,
    extra=1,
    can_delete=True
)

class FoodAnalysisForm(forms.Form):
    food_description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': '請描述您所吃的食物，例如：一碗牛肉麵、一份炒飯和一杯奶茶'}),
        label='食物描述'
    )

class SaveAnalysisToRecordForm(forms.ModelForm):
    class Meta:
        model = UserFoodRecord
        fields = ['name', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': '食物名稱',
            'image': '食物圖片（可選）'
        } 