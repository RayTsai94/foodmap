#!/usr/bin/env python
import os
import django
import requests
import time

# 設置Django環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ncufoodmap_backend.settings')
django.setup()

from restaurants.models import Restaurant, Category
from django.conf import settings

# Google Places API 設定
GOOGLE_PLACES_API_KEY = settings.GOOGLE_MAPS_API_KEY
PLACES_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
PLACES_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

# 中央大學座標
NCU_LOCATION = {
    'lat': 24.9677,
    'lng': 121.1892
}

def create_categories():
    """創建餐廳分類"""
    categories_data = [
        {'name': '中式料理', 'icon': 'fas fa-bowl-rice'},
        {'name': '日式料理', 'icon': 'fas fa-fish'},
        {'name': '韓式料理', 'icon': 'fas fa-pepper-hot'},
        {'name': '西式料理', 'icon': 'fas fa-hamburger'},
        {'name': '義式料理', 'icon': 'fas fa-pizza-slice'},
        {'name': '泰式料理', 'icon': 'fas fa-leaf'},
        {'name': '火鍋', 'icon': 'fas fa-fire'},
        {'name': '燒烤', 'icon': 'fas fa-fire-burner'},
        {'name': '飲料店', 'icon': 'fas fa-mug-hot'},
        {'name': '早餐店', 'icon': 'fas fa-bread-slice'},
        {'name': '便當', 'icon': 'fas fa-box'},
        {'name': '小吃', 'icon': 'fas fa-cookie-bite'},
        {'name': '咖啡廳', 'icon': 'fas fa-coffee'},
        {'name': '甜點', 'icon': 'fas fa-birthday-cake'},
    ]
    
    categories = {}
    for cat_data in categories_data:
        category, created = Category.objects.get_or_create(
            name=cat_data['name'],
            defaults={'icon': cat_data['icon']}
        )
        categories[cat_data['name']] = category
        if created:
            print(f"✅ 創建分類: {category.name}")
    
    return categories

def get_restaurant_category(types, name):
    """根據Google Places類型和名稱判斷餐廳分類"""
    category_mapping = {
        'chinese_restaurant': '中式料理',
        'japanese_restaurant': '日式料理',
        'korean_restaurant': '韓式料理',
        'italian_restaurant': '義式料理',
        'american_restaurant': '西式料理',
        'thai_restaurant': '泰式料理',
        'vietnamese_restaurant': '越式料理',
        'indian_restaurant': '印度料理',
        'mexican_restaurant': '墨西哥料理',
        'french_restaurant': '法式料理',
        'steak_house': '西式料理',
        'seafood_restaurant': '海鮮料理',
        'barbecue_restaurant': '燒烤',
        'fast_food_restaurant': '速食',
        'pizza_restaurant': '義式料理',
        'sushi_restaurant': '日式料理',
        'ramen_restaurant': '日式料理',
        'cafe': '咖啡廳',
        'bakery': '甜點',
        'ice_cream_shop': '甜點',
        'bubble_tea_store': '飲料店',
        'meal_takeaway': '便當',
        'food': '小吃',
    }
    
    # 檢查Google Places類型
    for place_type in types:
        if place_type in category_mapping:
            return category_mapping[place_type]
    
    # 根據餐廳名稱判斷
    name_lower = name.lower()
    if any(keyword in name_lower for keyword in ['火鍋', 'hot pot', '鍋']):
        return '火鍋'
    elif any(keyword in name_lower for keyword in ['拉麵', 'ramen', '壽司', 'sushi', '日式', '丼']):
        return '日式料理'
    elif any(keyword in name_lower for keyword in ['韓式', 'korean', '烤肉', '韓國']):
        return '韓式料理'
    elif any(keyword in name_lower for keyword in ['義大利', 'pizza', 'pasta', '披薩']):
        return '義式料理'
    elif any(keyword in name_lower for keyword in ['泰式', 'thai', '泰國']):
        return '泰式料理'
    elif any(keyword in name_lower for keyword in ['牛排', 'steak', '漢堡', 'burger']):
        return '西式料理'
    elif any(keyword in name_lower for keyword in ['咖啡', 'coffee', 'cafe', '星巴克', 'starbucks']):
        return '咖啡廳'
    elif any(keyword in name_lower for keyword in ['飲料', '茶', '50嵐', '清心', '可不可']):
        return '飲料店'
    elif any(keyword in name_lower for keyword in ['早餐', '美而美', '豐盛號']):
        return '早餐店'
    elif any(keyword in name_lower for keyword in ['便當', '池上', '悟饕']):
        return '便當'
    elif any(keyword in name_lower for keyword in ['麵', '麵店', '牛肉麵', '小吃']):
        return '小吃'
    else:
        return '中式料理'  # 預設分類

def search_nearby_restaurants(radius=2000):
    """搜索中央大學附近的餐廳"""
    all_restaurants = []
    next_page_token = None
    
    while True:
        params = {
            'location': f"{NCU_LOCATION['lat']},{NCU_LOCATION['lng']}",
            'radius': radius,
            'type': 'restaurant',
            'key': GOOGLE_PLACES_API_KEY,
            'language': 'zh-TW'
        }
        
        if next_page_token:
            params['pagetoken'] = next_page_token
        
        print(f"🔍 搜索半徑 {radius}m 內的餐廳...")
        response = requests.get(PLACES_SEARCH_URL, params=params)
        
        if response.status_code != 200:
            print(f"❌ API 請求失敗: {response.status_code}")
            break
        
        data = response.json()
        
        if data['status'] != 'OK':
            print(f"❌ Google Places API 錯誤: {data['status']}")
            if 'error_message' in data:
                print(f"錯誤訊息: {data['error_message']}")
            break
        
        restaurants = data.get('results', [])
        all_restaurants.extend(restaurants)
        
        print(f"✅ 找到 {len(restaurants)} 間餐廳")
        
        # 檢查是否有下一頁
        next_page_token = data.get('next_page_token')
        if not next_page_token:
            break
        
        # Google Places API 需要等待幾秒才能使用 next_page_token
        print("⏳ 等待 2 秒後繼續搜索...")
        time.sleep(2)
    
    return all_restaurants

def get_restaurant_details(place_id):
    """獲取餐廳詳細資訊"""
    params = {
        'place_id': place_id,
        'fields': 'name,formatted_address,formatted_phone_number,rating,user_ratings_total,price_level,opening_hours,website,types,geometry',
        'key': GOOGLE_PLACES_API_KEY,
        'language': 'zh-TW'
    }
    
    response = requests.get(PLACES_DETAILS_URL, params=params)
    
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'OK':
            return data['result']
    
    return None

def save_restaurants_to_database(restaurants_data, categories):
    """將餐廳數據保存到資料庫"""
    saved_count = 0
    
    for restaurant_data in restaurants_data:
        try:
            # 基本資訊
            name = restaurant_data.get('name', '未知餐廳')
            place_id = restaurant_data.get('place_id')
            
            # 檢查是否已存在
            if Restaurant.objects.filter(name=name).exists():
                print(f"⚠️  餐廳已存在: {name}")
                continue
            
            # 獲取詳細資訊
            details = get_restaurant_details(place_id)
            if not details:
                print(f"❌ 無法獲取餐廳詳細資訊: {name}")
                continue
            
            # 地址和座標
            address = details.get('formatted_address', restaurant_data.get('vicinity', ''))
            geometry = details.get('geometry', {})
            location = geometry.get('location', {})
            lat = location.get('lat')
            lng = location.get('lng')
            
            # 其他資訊
            phone = details.get('formatted_phone_number', '')
            website = details.get('website', '')
            rating = details.get('rating', 0)
            user_ratings_total = details.get('user_ratings_total', 0)
            
            # 營業時間
            opening_hours = details.get('opening_hours', {})
            is_open = opening_hours.get('open_now', True)
            
            # 餐廳類型
            types = details.get('types', [])
            category_name = get_restaurant_category(types, name)
            
            # 描述
            description = f"Google評分: {rating}⭐ ({user_ratings_total}則評論)"
            if not is_open:
                description += " | 目前休息中"
            
            # 創建餐廳
            restaurant = Restaurant.objects.create(
                name=name,
                address=address,
                phone=phone,
                description=description,
                website=website,
                lat=lat,
                lng=lng,
                is_active=True
            )
            
            # 添加分類
            if category_name in categories:
                restaurant.categories.add(categories[category_name])
            
            print(f"✅ 保存餐廳: {name} ({category_name})")
            saved_count += 1
            
            # 避免API請求過於頻繁
            time.sleep(0.1)
            
        except Exception as e:
            print(f"❌ 保存餐廳時發生錯誤: {restaurant_data.get('name', 'Unknown')} - {str(e)}")
    
    return saved_count

def main():
    """主函數"""
    print("=== 開始獲取中央大學附近的真實餐廳數據 ===")
    
    # 創建分類
    print("\n📁 創建餐廳分類...")
    categories = create_categories()
    
    # 搜索餐廳
    print("\n🔍 搜索附近餐廳...")
    restaurants_data = search_nearby_restaurants()
    
    if not restaurants_data:
        print("❌ 沒有找到餐廳數據")
        return
    
    print(f"\n📊 總共找到 {len(restaurants_data)} 間餐廳")
    
    # 保存到資料庫
    print("\n💾 保存餐廳數據到資料庫...")
    saved_count = save_restaurants_to_database(restaurants_data, categories)
    
    # 顯示結果
    print(f"\n=== 完成 ===")
    print(f"✅ 成功保存 {saved_count} 間餐廳")
    print(f"📊 資料庫統計:")
    print(f"   餐廳總數: {Restaurant.objects.count()}")
    print(f"   分類總數: {Category.objects.count()}")
    
    print(f"\n🎉 現在您可以在搜索功能中找到真實的餐廳了！")

if __name__ == "__main__":
    main() 