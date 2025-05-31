from django.contrib import admin
from .models import NutritionInfo, Ingredient, MenuItemIngredient, FoodPreference, MenuItemPreference, PersonalFoodRecord, PersonalNutritionSummary

# Register your models here.

@admin.register(NutritionInfo)
class NutritionInfoAdmin(admin.ModelAdmin):
    list_display = ['menu_item', 'calories', 'protein', 'carbs', 'fat']
    list_filter = ['menu_item__restaurant']
    search_fields = ['menu_item__name']

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']

@admin.register(MenuItemIngredient)
class MenuItemIngredientAdmin(admin.ModelAdmin):
    list_display = ['menu_item', 'ingredient', 'amount']
    list_filter = ['menu_item__restaurant']
    search_fields = ['menu_item__name', 'ingredient__name']

@admin.register(FoodPreference)
class FoodPreferenceAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'description']
    list_filter = ['type']
    search_fields = ['name']

@admin.register(MenuItemPreference)
class MenuItemPreferenceAdmin(admin.ModelAdmin):
    list_display = ['menu_item', 'preference', 'is_compatible']
    list_filter = ['preference__type', 'is_compatible']
    search_fields = ['menu_item__name', 'preference__name']

@admin.register(PersonalFoodRecord)
class PersonalFoodRecordAdmin(admin.ModelAdmin):
    list_display = ['user', 'food_description', 'meal_type', 'date_consumed', 'calories']
    list_filter = ['meal_type', 'date_consumed', 'user']
    search_fields = ['user__username', 'food_description']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('基本資訊', {
            'fields': ('user', 'food_description', 'meal_type', 'date_consumed')
        }),
        ('營養分析', {
            'fields': ('calories', 'protein', 'carbs', 'fat', 'fiber', 'sugar', 'sodium')
        }),
        ('AI 分析結果', {
            'fields': ('nutritional_analysis', 'health_impact', 'improvement_suggestions'),
            'classes': ('collapse',)
        }),
        ('系統資訊', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )

@admin.register(PersonalNutritionSummary)
class PersonalNutritionSummaryAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'total_calories', 'total_protein', 'meal_count']
    list_filter = ['date', 'user']
    search_fields = ['user__username']
    readonly_fields = ['meal_count']
