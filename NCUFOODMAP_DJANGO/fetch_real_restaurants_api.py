#!/usr/bin/env python
import os
import sys
import django
import requests
import time
from urllib.parse import urljoin
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

# 設置 Django 環境
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ncufoodmap_backend.settings')
django.setup()

from restaurants.models import Restaurant, Category
from django.conf import settings

# Google Places API 設定
GOOGLE_API_KEY = getattr(settings, 'GOOGLE_MAPS_API_KEY', '')
PLACES_API_URL = 'https://maps.googleapis.com/maps/api/place'

def get_places_nearby(location, radius=5000, place_type='restaurant'):
    """使用 Google Places API 搜尋附近的餐廳"""
    url = f"{PLACES_API_URL}/nearbysearch/json"
    
    params = {
        'location': location,
        'radius': radius,
        'type': place_type,
        'key': GOOGLE_API_KEY,
        'language': 'zh-TW'
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"API 請求失敗: {response.status_code}")
        return None

def get_place_details(place_id):
    """獲取餐廳詳細資訊"""
    url = f"{PLACES_API_URL}/details/json"
    
    params = {
        'place_id': place_id,
        'fields': 'name,formatted_address,formatted_phone_number,website,rating,photos,geometry,types,opening_hours,price_level',
        'key': GOOGLE_API_KEY,
        'language': 'zh-TW'
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get('result', {})
    else:
        print(f"詳細資訊請求失敗: {response.status_code}")
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
    else:
        print(f"照片下載失敗: {response.status_code}")
        return None

def categorize_restaurant(types):
    """根據 Google Places 類型分類餐廳"""
    category_mapping = {
        'chinese_restaurant': '中式料理',
        'japanese_restaurant': '日式料理',
        'korean_restaurant': '韓式料理',
        'american_restaurant': '西式料理',
        'italian_restaurant': '義式料理',
        'thai_restaurant': '泰式料理',
        'cafe': '咖啡廳',
        'bakery': '甜點店',
        'meal_takeaway': '小吃攤',
        'restaurant': '餐廳'
    }
    
    for place_type in types:
        if place_type in category_mapping:
            return category_mapping[place_type]
    
    # 根據名稱關鍵字判斷
    return '餐廳'  # 預設分類

def create_categories():
    """創建餐廳分類"""
    categories_data = [
        {'name': '中式料理', 'icon': 'fas fa-utensils'},
        {'name': '日式料理', 'icon': 'fas fa-fish'},
        {'name': '韓式料理', 'icon': 'fas fa-pepper-hot'},
        {'name': '西式料理', 'icon': 'fas fa-hamburger'},
        {'name': '義式料理', 'icon': 'fas fa-pizza-slice'},
        {'name': '泰式料理', 'icon': 'fas fa-leaf'},
        {'name': '咖啡廳', 'icon': 'fas fa-coffee'},
        {'name': '甜點店', 'icon': 'fas fa-birthday-cake'},
        {'name': '小吃攤', 'icon': 'fas fa-hotdog'},
        {'name': '餐廳', 'icon': 'fas fa-utensils'},
    ]
    
    created_categories = {}
    for cat_data in categories_data:
        category, created = Category.objects.get_or_create(
            name=cat_data['name'],
            defaults={'icon': cat_data['icon']}
        )
        created_categories[cat_data['name']] = category
        print(f"分類 '{category.name}' {'創建' if created else '已存在'}")
    
    return created_categories

def fetch_restaurants_from_api():
    """從 Google Places API 獲取餐廳數據"""
    if not GOOGLE_API_KEY:
        print("錯誤: 請在 settings.py 中設定 GOOGLE_MAPS_API_KEY")
        return
    
    categories = create_categories()
    
    # 中央大學周邊的搜尋點
    search_locations = [
        "24.9675,121.1944",  # 中央大學
        "24.9530,121.2260",  # 中壢火車站
        "24.9580,121.2160",  # 中壢市區
        "24.9620,121.2050",  # 內壢
        "24.9450,121.2350",  # 青埔
    ]
    
    total_created = 0
    
    for location in search_locations:
        print(f"\n搜尋位置: {location}")
        
        # 搜尋附近的餐廳
        places_data = get_places_nearby(location, radius=3000)
        
        if not places_data or 'results' not in places_data:
            print("無法獲取餐廳數據")
            continue
        
        for place in places_data['results']:
            # 檢查餐廳是否已存在
            if Restaurant.objects.filter(name=place['name']).exists():
                continue
            
            print(f"處理餐廳: {place['name']}")
            
            # 獲取詳細資訊
            details = get_place_details(place['place_id'])
            
            # 準備餐廳數據
            restaurant_data = {
                'name': place['name'],
                'address': details.get('formatted_address', place.get('vicinity', '')),
                'phone': details.get('formatted_phone_number', ''),
                'website': details.get('website', ''),
                'lat': place['geometry']['location']['lat'],
                'lng': place['geometry']['location']['lng'],
                'is_active': True,
                'description': f"Google評分: {place.get('rating', 0)}/5"
            }
            
            # 創建餐廳
            restaurant = Restaurant.objects.create(**restaurant_data)
            
            # 分類餐廳
            category_name = categorize_restaurant(place.get('types', []))
            if category_name in categories:
                restaurant.categories.add(categories[category_name])
            
            # 下載並保存照片
            if 'photos' in place and place['photos']:
                photo_reference = place['photos'][0]['photo_reference']
                photo_content = download_photo(photo_reference)
                
                if photo_content:
                    # 保存照片
                    photo_name = f"restaurant_{restaurant.id}_{int(time.time())}.jpg"
                    restaurant.image.save(
                        photo_name,
                        ContentFile(photo_content),
                        save=True
                    )
                    print(f"  - 照片已保存: {photo_name}")
            
            total_created += 1
            print(f"  - 餐廳已創建: {restaurant.name}")
            
            # API 限制，避免請求過快
            time.sleep(0.1)
    
    print(f"\n總共創建了 {total_created} 家真實餐廳")

def search_restaurants_by_keyword(keyword, location="24.9675,121.1944", radius=5000):
    """根據關鍵字搜尋特定類型的餐廳"""
    url = f"{PLACES_API_URL}/textsearch/json"
    
    params = {
        'query': f"{keyword} 餐廳 中壢",
        'location': location,
        'radius': radius,
        'key': GOOGLE_API_KEY,
        'language': 'zh-TW'
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"關鍵字搜尋失敗: {response.status_code}")
        return None

def fetch_restaurants_by_categories():
    """按分類搜尋餐廳，確保每個分類都有足夠的餐廳"""
    if not GOOGLE_API_KEY:
        print("錯誤: 請在 settings.py 中設定 GOOGLE_MAPS_API_KEY")
        return
    
    categories = create_categories()
    
    # 搜尋關鍵字對應
    search_keywords = {
        '中式料理': ['中式', '中餐', '台菜', '粵菜', '川菜', '湘菜'],
        '日式料理': ['日式', '日本料理', '壽司', '拉麵', '丼飯', '燒肉'],
        '韓式料理': ['韓式', '韓國料理', '烤肉', '韓式炸雞', '韓式火鍋'],
        '西式料理': ['西式', '美式', '牛排', '漢堡', '義大利麵'],
        '義式料理': ['義式', '義大利', '披薩', 'pizza', '義大利麵'],
        '泰式料理': ['泰式', '泰國料理', '泰式料理'],
        '咖啡廳': ['咖啡', 'cafe', '咖啡廳', '咖啡店'],
        '甜點店': ['甜點', '蛋糕', '麵包', '烘焙', '甜品'],
        '小吃攤': ['小吃', '夜市', '路邊攤', '快餐'],
    }
    
    total_created = 0
    
    for category_name, keywords in search_keywords.items():
        print(f"\n搜尋分類: {category_name}")
        category_count = 0
        
        for keyword in keywords:
            if category_count >= 20:  # 每個分類最多20家
                break
                
            print(f"  搜尋關鍵字: {keyword}")
            places_data = search_restaurants_by_keyword(keyword)
            
            if not places_data or 'results' not in places_data:
                continue
            
            for place in places_data['results'][:5]:  # 每個關鍵字最多5家
                if Restaurant.objects.filter(name=place['name']).exists():
                    continue
                
                print(f"    處理餐廳: {place['name']}")
                
                # 獲取詳細資訊
                details = get_place_details(place['place_id'])
                
                # 準備餐廳數據
                restaurant_data = {
                    'name': place['name'],
                    'address': details.get('formatted_address', place.get('formatted_address', '')),
                    'phone': details.get('formatted_phone_number', ''),
                    'website': details.get('website', ''),
                    'lat': place['geometry']['location']['lat'],
                    'lng': place['geometry']['location']['lng'],
                    'is_active': True,
                    'description': f"Google評分: {place.get('rating', 0)}/5 ⭐"
                }
                
                # 創建餐廳
                restaurant = Restaurant.objects.create(**restaurant_data)
                
                # 添加分類
                if category_name in categories:
                    restaurant.categories.add(categories[category_name])
                
                # 下載並保存照片
                if 'photos' in place and place['photos']:
                    photo_reference = place['photos'][0]['photo_reference']
                    photo_content = download_photo(photo_reference)
                    
                    if photo_content:
                        photo_name = f"restaurant_{restaurant.id}_{int(time.time())}.jpg"
                        restaurant.image.save(
                            photo_name,
                            ContentFile(photo_content),
                            save=True
                        )
                        print(f"      - 照片已保存")
                
                category_count += 1
                total_created += 1
                print(f"      - 餐廳已創建")
                
                # API 限制
                time.sleep(0.2)
        
        print(f"  分類 '{category_name}' 已添加 {category_count} 家餐廳")
    
    print(f"\n總共創建了 {total_created} 家真實餐廳")

if __name__ == '__main__':
    print("開始從 Google Places API 獲取真實餐廳數據...")
    print("這可能需要幾分鐘時間，請耐心等待...")
    
    # 清除之前的虛假數據（可選）
    # Restaurant.objects.all().delete()
    
    # 按分類搜尋餐廳
    fetch_restaurants_by_categories()
    
    print("真實餐廳數據獲取完成！") 