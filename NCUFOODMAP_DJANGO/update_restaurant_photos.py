#!/usr/bin/env python
import os
import django
import requests
import time
from django.core.files.base import ContentFile

# 設置Django環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ncufoodmap_backend.settings')
django.setup()

from restaurants.models import Restaurant
from django.conf import settings

# Google Places API 設定
GOOGLE_PLACES_API_KEY = settings.GOOGLE_MAPS_API_KEY
PLACES_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
PLACES_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
PLACES_PHOTO_URL = "https://maps.googleapis.com/maps/api/place/photo"

def download_restaurant_photo(photo_reference, restaurant_name, max_width=400):
    """下載餐廳照片"""
    try:
        photo_params = {
            'photoreference': photo_reference,
            'maxwidth': max_width,
            'key': GOOGLE_PLACES_API_KEY
        }
        
        print(f"📷 下載 {restaurant_name} 的照片...")
        response = requests.get(PLACES_PHOTO_URL, params=photo_params, stream=True)
        
        if response.status_code == 200:
            # 獲取文件擴展名
            content_type = response.headers.get('content-type', '')
            if 'jpeg' in content_type or 'jpg' in content_type:
                extension = '.jpg'
            elif 'png' in content_type:
                extension = '.png'
            else:
                extension = '.jpg'  # 默認為 jpg
            
            # 生成文件名
            safe_name = "".join(c for c in restaurant_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{safe_name[:30]}{extension}"
            
            # 創建 Django 文件對象
            photo_content = ContentFile(response.content, name=filename)
            print(f"✅ 成功下載照片: {filename}")
            return photo_content
        else:
            print(f"❌ 下載照片失敗: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 下載照片時發生錯誤: {str(e)}")
        return None

def search_restaurant_by_name_and_location(restaurant_name, lat, lng, radius=50):
    """根據名稱和位置搜索餐廳"""
    try:
        params = {
            'location': f"{lat},{lng}",
            'radius': radius,
            'keyword': restaurant_name,
            'type': 'restaurant',
            'key': GOOGLE_PLACES_API_KEY,
            'language': 'zh-TW'
        }
        
        response = requests.get(PLACES_SEARCH_URL, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'OK' and data.get('results'):
                return data['results'][0]  # 返回第一個結果
        
        return None
    except Exception as e:
        print(f"❌ 搜索餐廳時發生錯誤: {str(e)}")
        return None

def get_restaurant_photos(place_id):
    """獲取餐廳照片"""
    try:
        params = {
            'place_id': place_id,
            'fields': 'photos',
            'key': GOOGLE_PLACES_API_KEY,
            'language': 'zh-TW'
        }
        
        response = requests.get(PLACES_DETAILS_URL, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'OK':
                return data['result'].get('photos', [])
        
        return []
    except Exception as e:
        print(f"❌ 獲取餐廳照片時發生錯誤: {str(e)}")
        return []

def update_restaurant_photos():
    """為現有餐廳更新照片"""
    restaurants = Restaurant.objects.filter(image='')  # 只更新沒有照片的餐廳
    total_restaurants = restaurants.count()
    updated_count = 0
    
    print(f"🔍 找到 {total_restaurants} 間沒有照片的餐廳")
    
    for i, restaurant in enumerate(restaurants, 1):
        print(f"\n[{i}/{total_restaurants}] 處理餐廳: {restaurant.name}")
        
        try:
            # 搜索餐廳
            place_data = search_restaurant_by_name_and_location(
                restaurant.name, restaurant.lat, restaurant.lng
            )
            
            if not place_data:
                print(f"⚠️  找不到餐廳: {restaurant.name}")
                continue
            
            place_id = place_data.get('place_id')
            if not place_id:
                print(f"⚠️  沒有 place_id: {restaurant.name}")
                continue
            
            # 獲取照片
            photos = get_restaurant_photos(place_id)
            
            if not photos:
                print(f"⚠️  沒有找到照片: {restaurant.name}")
                continue
            
            # 下載第一張照片
            first_photo = photos[0]
            photo_reference = first_photo.get('photo_reference')
            
            if photo_reference:
                photo_content = download_restaurant_photo(photo_reference, restaurant.name)
                if photo_content:
                    restaurant.image.save(photo_content.name, photo_content, save=True)
                    print(f"✅ 已更新 {restaurant.name} 的照片")
                    updated_count += 1
                
                # 避免API請求過於頻繁
                time.sleep(0.3)
            
        except Exception as e:
            print(f"❌ 處理餐廳時發生錯誤: {restaurant.name} - {str(e)}")
        
        # 每10個餐廳後稍作停頓
        if i % 10 == 0:
            print("⏳ 稍作停頓避免API限制...")
            time.sleep(2)
    
    return updated_count

def main():
    """主函數"""
    print("=== 開始為現有餐廳更新真實照片 ===")
    
    # 檢查資料庫狀態
    total_restaurants = Restaurant.objects.count()
    restaurants_with_photos = Restaurant.objects.exclude(image='').count()
    restaurants_without_photos = Restaurant.objects.filter(image='').count()
    
    print(f"\n📊 資料庫狀態:")
    print(f"   餐廳總數: {total_restaurants}")
    print(f"   有照片的餐廳: {restaurants_with_photos}")
    print(f"   沒有照片的餐廳: {restaurants_without_photos}")
    
    if restaurants_without_photos == 0:
        print("\n🎉 所有餐廳都已經有照片了！")
        return
    
    # 更新照片
    print(f"\n📷 開始為 {restaurants_without_photos} 間餐廳更新照片...")
    updated_count = update_restaurant_photos()
    
    # 顯示結果
    print(f"\n=== 完成 ===")
    print(f"✅ 成功更新 {updated_count} 間餐廳的照片")
    
    # 重新檢查狀態
    restaurants_with_photos_after = Restaurant.objects.exclude(image='').count()
    restaurants_without_photos_after = Restaurant.objects.filter(image='').count()
    
    print(f"\n📊 更新後狀態:")
    print(f"   有照片的餐廳: {restaurants_with_photos_after}")
    print(f"   沒有照片的餐廳: {restaurants_without_photos_after}")
    
    print(f"\n🎉 現在您可以在網站上看到真實的餐廳照片了！")

if __name__ == "__main__":
    main() 