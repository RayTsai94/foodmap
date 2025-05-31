#!/usr/bin/env python
import os
import sys
import django

# 設置 Django 環境
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ncufoodmap_backend.settings')
django.setup()

from restaurants.models import Restaurant, Category

def check_restaurant_stats():
    """檢查餐廳統計"""
    print("=== 餐廳分類統計 ===")
    
    categories = Category.objects.all()
    total_restaurants = 0
    
    for category in categories:
        count = Restaurant.objects.filter(categories=category).count()
        status = "✅" if count >= 50 else "❌"
        print(f"{status} {category.name}: {count} 家餐廳")
        total_restaurants += count
    
    print(f"\n總共有 {Restaurant.objects.count()} 家餐廳")
    print(f"有照片的餐廳: {Restaurant.objects.exclude(image='').count()} 家")
    print(f"沒有照片的餐廳: {Restaurant.objects.filter(image='').count()} 家")

if __name__ == '__main__':
    check_restaurant_stats() 