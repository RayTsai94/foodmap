#!/usr/bin/env python
import os
import sys
import django
import requests
import time
from django.core.files.base import ContentFile

# 設置 Django 環境
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ncufoodmap_backend.settings')
django.setup()

from restaurants.models import Restaurant, Category
from django.conf import settings

# Google Places API 設定
GOOGLE_API_KEY = getattr(settings, 'GOOGLE_MAPS_API_KEY', '')
PLACES_API_URL = 'https://maps.googleapis.com/maps/api/place'

def search_restaurant_by_name_and_address(name, address):
    """根據餐廳名稱和地址搜尋 Google Places"""
    url = f"{PLACES_API_URL}/textsearch/json"
    
    # 清理地址，只保留主要部分
    address_parts = address.split(',')
    main_address = address_parts[0] if address_parts else address
    
    params = {
        'query': f"{name} {main_address}",
        'key': GOOGLE_API_KEY,
        'language': 'zh-TW'
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if 'results' in data and data['results']:
            return data['results'][0]  # 返回第一個結果
    return None

def get_place_details(place_id):
    """獲取餐廳詳細資訊"""
    url = f"{PLACES_API_URL}/details/json"
    
    params = {
        'place_id': place_id,
        'fields': 'photos,rating,website,formatted_phone_number',
        'key': GOOGLE_API_KEY,
        'language': 'zh-TW'
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get('result', {})
    return {}

def download_photo(photo_reference, max_width=400):
    """下載餐廳照片"""
    url = f"{PLACES_API_URL}/photo"
    
    params = {
        'photoreference': photo_reference,
        'maxwidth': max_width,
        'key': GOOGLE_API_KEY
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.content
    return None

def update_restaurant_photos():
    """為沒有照片的餐廳補充照片"""
    if not GOOGLE_API_KEY:
        print("錯誤: 請在 settings.py 中設定 GOOGLE_MAPS_API_KEY")
        return
    
    # 獲取沒有照片的餐廳
    restaurants_without_photos = Restaurant.objects.filter(image='')
    total_count = restaurants_without_photos.count()
    
    print(f"找到 {total_count} 家沒有照片的餐廳")
    
    updated_count = 0
    
    for i, restaurant in enumerate(restaurants_without_photos, 1):
        print(f"[{i}/{total_count}] 處理餐廳: {restaurant.name}")
        
        # 搜尋餐廳
        place_data = search_restaurant_by_name_and_address(restaurant.name, restaurant.address)
        
        if not place_data:
            print(f"  - 找不到餐廳資訊")
            continue
        
        # 獲取詳細資訊
        details = get_place_details(place_data['place_id'])
        
        # 更新餐廳資訊
        updated = False
        
        # 更新評分描述
        if 'rating' in place_data:
            restaurant.description = f"Google評分: {place_data['rating']}/5 ⭐"
            updated = True
        
        # 更新電話
        if 'formatted_phone_number' in details and not restaurant.phone:
            restaurant.phone = details['formatted_phone_number']
            updated = True
        
        # 更新網站
        if 'website' in details and not restaurant.website:
            restaurant.website = details['website']
            updated = True
        
        # 下載並保存照片
        if 'photos' in place_data and place_data['photos']:
            photo_reference = place_data['photos'][0]['photo_reference']
            photo_content = download_photo(photo_reference)
            
            if photo_content:
                photo_name = f"restaurant_{restaurant.id}_{int(time.time())}.jpg"
                restaurant.image.save(
                    photo_name,
                    ContentFile(photo_content),
                    save=False  # 稍後一起保存
                )
                print(f"  - 照片已下載")
                updated = True
            else:
                print(f"  - 照片下載失敗")
        else:
            print(f"  - 沒有可用照片")
        
        if updated:
            restaurant.save()
            updated_count += 1
            print(f"  - 餐廳資訊已更新")
        
        # API 限制
        time.sleep(0.2)
        
        # 每處理50家餐廳顯示進度
        if i % 50 == 0:
            print(f"\n已處理 {i}/{total_count} 家餐廳，成功更新 {updated_count} 家\n")
    
    print(f"\n完成！總共更新了 {updated_count} 家餐廳的照片和資訊")

def clean_fake_restaurants():
    """清理明顯的虛假餐廳數據"""
    print("開始清理虛假餐廳數據...")
    
    # 刪除明顯虛假的餐廳名稱
    fake_patterns = [
        '美味餐廳', '好吃小館', '香香餐廳', '美食天地', '好味道',
        '老字號', '傳統美食', '家常菜', '小廚房', '美食坊'
    ]
    
    deleted_count = 0
    for pattern in fake_patterns:
        fake_restaurants = Restaurant.objects.filter(name__icontains=pattern)
        count = fake_restaurants.count()
        if count > 0:
            fake_restaurants.delete()
            deleted_count += count
            print(f"  刪除了 {count} 家包含 '{pattern}' 的餐廳")
    
    print(f"總共刪除了 {deleted_count} 家虛假餐廳")

def verify_restaurant_data():
    """驗證餐廳數據的真實性"""
    print("\n=== 餐廳數據驗證 ===")
    
    total_restaurants = Restaurant.objects.count()
    restaurants_with_photos = Restaurant.objects.exclude(image='').count()
    restaurants_with_phone = Restaurant.objects.exclude(phone='').count()
    restaurants_with_website = Restaurant.objects.exclude(website='').count()
    restaurants_with_google_rating = Restaurant.objects.filter(description__icontains='Google評分').count()
    
    print(f"總餐廳數: {total_restaurants}")
    print(f"有照片的餐廳: {restaurants_with_photos} ({restaurants_with_photos/total_restaurants*100:.1f}%)")
    print(f"有電話的餐廳: {restaurants_with_phone} ({restaurants_with_phone/total_restaurants*100:.1f}%)")
    print(f"有網站的餐廳: {restaurants_with_website} ({restaurants_with_website/total_restaurants*100:.1f}%)")
    print(f"有Google評分的餐廳: {restaurants_with_google_rating} ({restaurants_with_google_rating/total_restaurants*100:.1f}%)")
    
    # 檢查每個分類的數量
    print("\n=== 分類統計 ===")
    categories = Category.objects.all()
    for category in categories:
        count = Restaurant.objects.filter(categories=category).count()
        status = "✅" if count >= 50 else "❌"
        print(f"{status} {category.name}: {count} 家餐廳")

if __name__ == '__main__':
    print("開始更新真實餐廳數據...")
    
    # 1. 清理虛假數據
    clean_fake_restaurants()
    
    # 2. 為餐廳補充照片和資訊
    update_restaurant_photos()
    
    # 3. 驗證數據
    verify_restaurant_data()
    
    print("\n真實餐廳數據更新完成！") 