from django.contrib import admin
from .models import Category, Restaurant, Review, MenuItem

# 自訂管理介面
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'phone', 'created_at', 'is_active')
    list_filter = ('is_active', 'categories')
    search_fields = ('name', 'address')
    date_hierarchy = 'created_at'

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'author', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('author', 'comment')

class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'price', 'is_vegetarian', 'is_spicy', 'is_available')
    list_filter = ('is_vegetarian', 'is_spicy', 'is_available', 'restaurant')
    search_fields = ('name', 'description')

# 註冊模型
admin.site.register(Category)
admin.site.register(Restaurant, RestaurantAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(MenuItem, MenuItemAdmin)
