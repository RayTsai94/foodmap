#!/usr/bin/env python
import os
import django

# 設置Django環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ncufoodmap_backend.settings')
django.setup()

from restaurants.models import Restaurant, Category

def check_restaurant_data():
    """檢查餐廳數據"""
    restaurant_count = Restaurant.objects.count()
    category_count = Category.objects.count()
    
    print(f"=== 餐廳數據檢查 ===")
    print(f"餐廳總數: {restaurant_count}")
    print(f"分類總數: {category_count}")
    
    if restaurant_count > 0:
        print(f"\n前5個餐廳:")
        for i, restaurant in enumerate(Restaurant.objects.all()[:5], 1):
            print(f"{i}. {restaurant.name}")
            print(f"   地址: {restaurant.address}")
            print(f"   座標: ({restaurant.lat}, {restaurant.lng})")
            print(f"   分類: {[cat.name for cat in restaurant.categories.all()]}")
            print(f"   是否啟用: {restaurant.is_active}")
            print()
    else:
        print("⚠️  沒有找到餐廳數據")
        
    if category_count > 0:
        print("分類列表:")
        for category in Category.objects.all():
            restaurant_in_category = category.restaurants.filter(is_active=True).count()
            print(f"- {category.name} ({restaurant_in_category}間餐廳)")
    else:
        print("⚠️  沒有找到分類數據")

if __name__ == "__main__":
    check_restaurant_data() 