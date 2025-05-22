from django.db import models
from restaurants.models import Restaurant, MenuItem

# Create your models here.
class NutritionInfo(models.Model):
    menu_item = models.OneToOneField(MenuItem, on_delete=models.CASCADE, related_name='nutrition')
    calories = models.IntegerField()
    protein = models.FloatField(help_text='以克為單位')
    carbs = models.FloatField(help_text='以克為單位')
    fat = models.FloatField(help_text='以克為單位')
    fiber = models.FloatField(help_text='以克為單位', null=True, blank=True)
    sugar = models.FloatField(help_text='以克為單位', null=True, blank=True)
    sodium = models.FloatField(help_text='以毫克為單位', null=True, blank=True)
    
    def __str__(self):
        return f"營養資訊: {self.menu_item.name}"

class Ingredient(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class MenuItemIngredient(models.Model):
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='ingredients')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='menu_items')
    amount = models.CharField(max_length=50, blank=True)  # 例如: "2 湯匙", "100克"
    
    def __str__(self):
        return f"{self.ingredient.name} in {self.menu_item.name}"

class FoodPreference(models.Model):
    PREFERENCE_TYPES = (
        ('ALLERGY', '過敏原'),
        ('DIET', '飲食習慣'),
        ('TASTE', '口味偏好'),
    )
    
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=PREFERENCE_TYPES)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

class MenuItemPreference(models.Model):
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='preferences')
    preference = models.ForeignKey(FoodPreference, on_delete=models.CASCADE, related_name='menu_items')
    is_compatible = models.BooleanField(default=True)
    
    def __str__(self):
        compatibility = "適合" if self.is_compatible else "不適合"
        return f"{self.menu_item.name} {compatibility} {self.preference.name}"
