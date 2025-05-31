from django.db import models
from restaurants.models import Restaurant, MenuItem
from django.contrib.auth.models import User

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

class PersonalFoodRecord(models.Model):
    """個人飲食記錄"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='food_records')
    food_description = models.TextField(help_text='描述您吃的食物，例如：一碗牛肉麵加滷蛋')
    meal_type = models.CharField(max_length=20, choices=[
        ('breakfast', '早餐'),
        ('lunch', '午餐'),
        ('dinner', '晚餐'),
        ('snack', '點心')
    ], default='lunch')
    date_consumed = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # AI 分析結果
    calories = models.IntegerField(null=True, blank=True)
    protein = models.FloatField(null=True, blank=True)
    carbs = models.FloatField(null=True, blank=True)
    fat = models.FloatField(null=True, blank=True)
    fiber = models.FloatField(null=True, blank=True)
    sugar = models.FloatField(null=True, blank=True)
    sodium = models.FloatField(null=True, blank=True)
    
    # AI 分析文字結果
    nutritional_analysis = models.TextField(blank=True)
    health_impact = models.TextField(blank=True)
    improvement_suggestions = models.JSONField(default=list, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.food_description[:50]} ({self.date_consumed})"

class PersonalNutritionSummary(models.Model):
    """個人營養總結（按日期）"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='nutrition_summaries')
    date = models.DateField()
    
    total_calories = models.IntegerField(default=0)
    total_protein = models.FloatField(default=0)
    total_carbs = models.FloatField(default=0)
    total_fat = models.FloatField(default=0)
    total_fiber = models.FloatField(default=0)
    total_sugar = models.FloatField(default=0)
    total_sodium = models.FloatField(default=0)
    
    meal_count = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.user.username} - {self.date} 營養總結"
