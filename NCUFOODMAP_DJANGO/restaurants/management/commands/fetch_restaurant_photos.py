import os
import requests
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.conf import settings
from restaurants.models import Restaurant
import time

class Command(BaseCommand):
    help = '使用 Google Places API 自動抓取餐廳照片'

    def add_arguments(self, parser):
        parser.add_argument(
            '--api-key',
            type=str,
            help='Google Places API Key',
            required=True
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='限制處理的餐廳數量'
        )

    def handle(self, *args, **options):
        api_key = options['api_key']
        limit = options['limit']
        
        # 獲取沒有圖片的餐廳
        restaurants = Restaurant.objects.filter(image__isnull=True)
        if limit:
            restaurants = restaurants[:limit]
            
        self.stdout.write(f'找到 {restaurants.count()} 個需要照片的餐廳')
        
        success_count = 0
        fail_count = 0
        
        for restaurant in restaurants:
            try:
                self.stdout.write(f'處理餐廳: {restaurant.name}')
                
                # 使用 Google Places API 搜尋餐廳
                photo_url = self.get_restaurant_photo(restaurant, api_key)
                
                if photo_url:
                    # 下載並保存照片
                    if self.download_and_save_photo(restaurant, photo_url):
                        success_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ 成功為 {restaurant.name} 下載照片')
                        )
                    else:
                        fail_count += 1
                        self.stdout.write(
                            self.style.ERROR(f'✗ 下載照片失敗: {restaurant.name}')
                        )
                else:
                    fail_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'⚠ 找不到照片: {restaurant.name}')
                    )
                
                # API 請求間隔，避免超過限制
                time.sleep(0.5)
                
            except Exception as e:
                fail_count += 1
                self.stdout.write(
                    self.style.ERROR(f'✗ 處理錯誤 {restaurant.name}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n完成！成功: {success_count}, 失敗: {fail_count}'
            )
        )

    def get_restaurant_photo(self, restaurant, api_key):
        """使用 Google Places API 搜尋餐廳照片"""
        
        # Text Search API
        search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        search_params = {
            'query': f"{restaurant.name} {restaurant.address}",
            'key': api_key,
            'fields': 'place_id,photos'
        }
        
        try:
            response = requests.get(search_url, params=search_params)
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                place = data['results'][0]
                
                if 'photos' in place and place['photos']:
                    photo_reference = place['photos'][0]['photo_reference']
                    
                    # Photo API
                    photo_url = "https://maps.googleapis.com/maps/api/place/photo"
                    photo_params = {
                        'photoreference': photo_reference,
                        'maxwidth': 800,
                        'key': api_key
                    }
                    
                    # 獲取實際照片 URL
                    photo_response = requests.get(photo_url, params=photo_params, allow_redirects=False)
                    if photo_response.status_code == 302:
                        return photo_response.headers.get('Location')
                    else:
                        return f"{photo_url}?{requests.compat.urlencode(photo_params)}"
            
            return None
            
        except Exception as e:
            self.stdout.write(f"API 請求錯誤: {str(e)}")
            return None

    def download_and_save_photo(self, restaurant, photo_url):
        """下載並保存餐廳照片"""
        try:
            response = requests.get(photo_url, timeout=30)
            response.raise_for_status()
            
            # 生成檔案名稱
            file_extension = 'jpg'  # Google Photos 通常是 JPG
            filename = f"{restaurant.name.replace(' ', '_').replace('/', '_')}.{file_extension}"
            
            # 保存檔案
            restaurant.image.save(
                filename,
                ContentFile(response.content),
                save=True
            )
            
            return True
            
        except Exception as e:
            self.stdout.write(f"下載錯誤: {str(e)}")
            return False 