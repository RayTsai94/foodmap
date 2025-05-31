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

def get_places_nearby(location, radius=10000, place_type='restaurant'):
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

def search_restaurants_by_keyword(keyword, location="24.9675,121.1944", radius=15000):
    """根據關鍵字搜尋特定類型的餐廳"""
    url = f"{PLACES_API_URL}/textsearch/json"
    
    params = {
        'query': f"{keyword} 餐廳 桃園",
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

def get_next_page_results(next_page_token):
    """獲取下一頁的搜尋結果"""
    url = f"{PLACES_API_URL}/textsearch/json"
    
    params = {
        'pagetoken': next_page_token,
        'key': GOOGLE_API_KEY,
        'language': 'zh-TW'
    }
    
    # 需要等待一下才能使用 next_page_token
    time.sleep(2)
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"下一頁搜尋失敗: {response.status_code}")
        return None

def categorize_restaurant(types, name):
    """根據 Google Places 類型和名稱分類餐廳"""
    # 先根據類型判斷
    type_mapping = {
        'chinese_restaurant': '中式料理',
        'japanese_restaurant': '日式料理',
        'korean_restaurant': '韓式料理',
        'american_restaurant': '西式料理',
        'italian_restaurant': '義式料理',
        'thai_restaurant': '泰式料理',
        'cafe': '咖啡廳',
        'bakery': '甜點店',
        'meal_takeaway': '小吃攤',
    }
    
    for place_type in types:
        if place_type in type_mapping:
            return type_mapping[place_type]
    
    # 根據名稱關鍵字判斷
    name_lower = name.lower()
    if any(keyword in name_lower for keyword in ['中式', '中餐', '台菜', '粵菜', '川菜', '湘菜', '客家', '港式']):
        return '中式料理'
    elif any(keyword in name_lower for keyword in ['日式', '日本', '壽司', '拉麵', '丼', '燒肉', 'sushi', 'ramen']):
        return '日式料理'
    elif any(keyword in name_lower for keyword in ['韓式', '韓國', '烤肉', '炸雞', '部隊鍋', 'korean']):
        return '韓式料理'
    elif any(keyword in name_lower for keyword in ['美式', '西式', '牛排', '漢堡', 'burger', 'steak']):
        return '西式料理'
    elif any(keyword in name_lower for keyword in ['義式', '義大利', '披薩', 'pizza', 'pasta', 'italian']):
        return '義式料理'
    elif any(keyword in name_lower for keyword in ['泰式', '泰國', 'thai']):
        return '泰式料理'
    elif any(keyword in name_lower for keyword in ['咖啡', 'coffee', 'cafe']):
        return '咖啡廳'
    elif any(keyword in name_lower for keyword in ['甜點', '蛋糕', '麵包', '烘焙', 'cake', 'bakery']):
        return '甜點店'
    elif any(keyword in name_lower for keyword in ['小吃', '夜市', '路邊', '快餐']):
        return '小吃攤'
    
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

def fetch_restaurants_to_target():
    """獲取餐廳直到每個分類都有50個以上"""
    if not GOOGLE_API_KEY:
        print("錯誤: 請在 settings.py 中設定 GOOGLE_MAPS_API_KEY")
        return
    
    categories = create_categories()
    target_count = 50
    
    # 擴展的搜尋關鍵字
    search_keywords = {
        '中式料理': [
            '中式餐廳', '中餐廳', '台菜', '粵菜', '川菜', '湘菜', '客家菜', '港式茶餐廳',
            '中式料理', '台灣料理', '廣東菜', '四川菜', '湖南菜', '江浙菜', '北京菜',
            '上海菜', '東北菜', '福建菜', '潮州菜', '港式飲茶', '茶餐廳', '中式快餐'
        ],
        '日式料理': [
            '日式餐廳', '日本料理', '壽司', '拉麵', '丼飯', '燒肉', '居酒屋', '日式火鍋',
            '日式定食', '天婦羅', '烏龍麵', '蕎麥麵', '日式燒烤', '日式咖哩', '日式甜點',
            '日式便當', '日式小菜', '日式串燒', '日式鐵板燒', '日式涮涮鍋'
        ],
        '韓式料理': [
            '韓式餐廳', '韓國料理', '韓式烤肉', '韓式炸雞', '韓式火鍋', '部隊鍋', '石鍋拌飯',
            '韓式燒烤', '韓式泡菜', '韓式冷麵', '韓式年糕', '韓式海鮮煎餅', '韓式豆腐鍋',
            '韓式辣炒年糕', '韓式烤肉', '韓式料理店'
        ],
        '西式料理': [
            '西式餐廳', '美式餐廳', '牛排館', '漢堡店', '義大利麵', '西餐廳', '美式料理',
            '歐式料理', '法式料理', '德式料理', '西式早餐', '西式快餐', '牛排屋',
            '漢堡餐廳', '西式簡餐', '歐陸料理', '地中海料理'
        ],
        '義式料理': [
            '義式餐廳', '義大利料理', '披薩店', '義大利麵', '義式咖啡', '義式冰淇淋',
            '義式烘焙', '義式簡餐', '義式pizza', '義式燉飯', '義式前菜', '義式甜點'
        ],
        '泰式料理': [
            '泰式餐廳', '泰國料理', '泰式火鍋', '泰式咖哩', '泰式炒河粉', '泰式酸辣湯',
            '泰式沙拉', '泰式烤肉', '泰式海鮮', '泰式甜點', '泰式飲品', '泰式小吃'
        ],
        '咖啡廳': [
            '咖啡廳', '咖啡店', '咖啡館', 'cafe', '精品咖啡', '手沖咖啡', '義式咖啡',
            '咖啡烘焙', '咖啡輕食', '下午茶', '咖啡甜點', '咖啡早餐', '咖啡簡餐'
        ],
        '甜點店': [
            '甜點店', '蛋糕店', '麵包店', '烘焙坊', '甜品店', '冰淇淋店', '手工甜點',
            '法式甜點', '日式甜點', '台式甜點', '巧克力專賣', '馬卡龍', '泡芙', '司康'
        ],
        '小吃攤': [
            '小吃店', '夜市小吃', '路邊攤', '快餐店', '便當店', '滷味', '鹽酥雞',
            '雞排', '珍珠奶茶', '飲料店', '早餐店', '宵夜', '台式小吃', '傳統小吃'
        ]
    }
    
    # 擴大搜尋範圍的地點
    search_locations = [
        "24.9675,121.1944",  # 中央大學
        "24.9530,121.2260",  # 中壢火車站
        "24.9580,121.2160",  # 中壢市區
        "24.9620,121.2050",  # 內壢
        "24.9450,121.2350",  # 青埔
        "24.9900,121.3100",  # 桃園市區
        "25.0478,121.5170",  # 台北車站
        "24.8066,120.9686",  # 新竹市區
    ]
    
    total_created = 0
    
    for category_name, keywords in search_keywords.items():
        current_count = Restaurant.objects.filter(categories__name=category_name).count()
        print(f"\n分類 '{category_name}' 目前有 {current_count} 家餐廳")
        
        if current_count >= target_count:
            print(f"  已達到目標數量 {target_count}，跳過")
            continue
        
        needed = target_count - current_count
        category_created = 0
        
        for location in search_locations:
            if category_created >= needed:
                break
                
            print(f"  在位置 {location} 搜尋...")
            
            for keyword in keywords:
                if category_created >= needed:
                    break
                    
                print(f"    搜尋關鍵字: {keyword}")
                places_data = search_restaurants_by_keyword(keyword, location, radius=20000)
                
                if not places_data or 'results' not in places_data:
                    continue
                
                # 處理第一頁結果
                for place in places_data['results']:
                    if category_created >= needed:
                        break
                        
                    if Restaurant.objects.filter(name=place['name']).exists():
                        continue
                    
                    # 檢查是否符合分類
                    detected_category = categorize_restaurant(place.get('types', []), place['name'])
                    if detected_category != category_name:
                        continue
                    
                    print(f"      處理餐廳: {place['name']}")
                    
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
                    
                    try:
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
                                print(f"        - 照片已保存")
                        
                        category_created += 1
                        total_created += 1
                        print(f"        - 餐廳已創建 ({category_created}/{needed})")
                        
                        # API 限制
                        time.sleep(0.3)
                        
                    except Exception as e:
                        print(f"        - 創建餐廳失敗: {e}")
                        continue
                
                # 處理下一頁結果（如果有的話）
                if 'next_page_token' in places_data and category_created < needed:
                    print(f"      獲取下一頁結果...")
                    next_page_data = get_next_page_results(places_data['next_page_token'])
                    
                    if next_page_data and 'results' in next_page_data:
                        for place in next_page_data['results']:
                            if category_created >= needed:
                                break
                                
                            if Restaurant.objects.filter(name=place['name']).exists():
                                continue
                            
                            # 檢查是否符合分類
                            detected_category = categorize_restaurant(place.get('types', []), place['name'])
                            if detected_category != category_name:
                                continue
                            
                            print(f"        處理餐廳: {place['name']}")
                            
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
                            
                            try:
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
                                        print(f"          - 照片已保存")
                                
                                category_created += 1
                                total_created += 1
                                print(f"          - 餐廳已創建 ({category_created}/{needed})")
                                
                                # API 限制
                                time.sleep(0.3)
                                
                            except Exception as e:
                                print(f"          - 創建餐廳失敗: {e}")
                                continue
        
        final_count = Restaurant.objects.filter(categories__name=category_name).count()
        print(f"  分類 '{category_name}' 最終有 {final_count} 家餐廳")
    
    print(f"\n總共新增了 {total_created} 家真實餐廳")
    
    # 顯示最終統計
    print("\n=== 最終統計 ===")
    for category_name in search_keywords.keys():
        count = Restaurant.objects.filter(categories__name=category_name).count()
        status = "✅" if count >= target_count else "❌"
        print(f"{status} {category_name}: {count} 家餐廳")

if __name__ == '__main__':
    print("開始獲取更多真實餐廳數據，確保每個分類都有50個以上...")
    print("這可能需要較長時間，請耐心等待...")
    
    fetch_restaurants_to_target()
    
    print("餐廳數據補充完成！") 