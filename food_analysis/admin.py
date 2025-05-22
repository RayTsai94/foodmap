from django.contrib import admin
from .models import NutritionInfo, Ingredient, MenuItemIngredient, FoodPreference, MenuItemPreference

# 自訂管理介面
class NutritionInfoAdmin(admin.ModelAdmin):
    list_display = ('menu_item', 'calories', 'protein', 'carbs', 'fat')
    search_fields = ('menu_item__name',)

class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', 'description')

class MenuItemIngredientAdmin(admin.ModelAdmin):
    list_display = ('menu_item', 'ingredient', 'amount')
    list_filter = ('ingredient', 'menu_item__restaurant')
    search_fields = ('menu_item__name', 'ingredient__name')

class FoodPreferenceAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'description')
    list_filter = ('type',)
    search_fields = ('name', 'description')

class MenuItemPreferenceAdmin(admin.ModelAdmin):
    list_display = ('menu_item', 'preference', 'is_compatible')
    list_filter = ('preference', 'is_compatible')
    search_fields = ('menu_item__name', 'preference__name')

# 註冊模型
admin.site.register(NutritionInfo, NutritionInfoAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(MenuItemIngredient, MenuItemIngredientAdmin)
admin.site.register(FoodPreference, FoodPreferenceAdmin)
admin.site.register(MenuItemPreference, MenuItemPreferenceAdmin)
