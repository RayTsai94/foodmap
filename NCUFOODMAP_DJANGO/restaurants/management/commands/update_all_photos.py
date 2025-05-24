import os
import requests
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from restaurants.models import Restaurant
import time

class Command(BaseCommand):
    help = '更新所有餐廳照片（包括已有照片的餐廳）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--api-key',
            type=str,
            help='Google Places API Key',
            required=True
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='強制更新所有餐廳照片，包括已有照片的餐廳'
        )

    def handle(self, *args, **options):
        api_key = options['api_key']
        force_update = options['force']
        
        if force_update:
            restaurants = Restaurant.objects.all()
            self.stdout.write('強制更新所有餐廳照片')
        else:
            restaurants = Restaurant.objects.filter(image__isnull=True)
            self.stdout.write('只更新沒有照片的餐廳')
            
        self.stdout.write(f'找到 {restaurants.count()} 個餐廳需要處理')
        
        success_count = 0
        fail_count = 0
        
        for i, restaurant in enumerate(restaurants, 1):
            try:
                self.stdout.write(f'[{i}/{restaurants.count()}] 處理: {restaurant.name}')
                
                # 獲取照片
                photo_url = self.get_restaurant_photo(restaurant, api_key)
                
                if photo_url:
                    if self.download_and_save_photo(restaurant, photo_url):
                        success_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ {restaurant.name} - 照片更新成功')
                        )
                    else:
                        fail_count += 1
                else:
                    fail_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'⚠ {restaurant.name} - 找不到照片')
                    )
                
                # API 限制：每秒最多請求
                time.sleep(1)
                
            except Exception as e:
                fail_count += 1
                self.stdout.write(
                    self.style.ERROR(f'✗ {restaurant.name} - 錯誤: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n=== 完成 ===\n成功: {success_count}\n失敗: {fail_count}')
        )

    def get_restaurant_photo(self, restaurant, api_key):
        """搜尋餐廳照片"""
        search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        
        # 先用餐廳名稱 + 地址搜尋
        query = f"{restaurant.name} {restaurant.address}"
        
        search_params = {
            'query': query,
            'key': api_key,
            'type': 'restaurant'
        }
        
        try:
            response = requests.get(search_url, params=search_params, timeout=10)
            data = response.json()
            
            if data['status'] == 'OK' and data.get('results'):
                for place in data['results']:
                    if 'photos' in place and place['photos']:
                        photo_reference = place['photos'][0]['photo_reference']
                        
                        # 構建照片 URL
                        photo_url = "https://maps.googleapis.com/maps/api/place/photo"
                        photo_params = {
                            'photoreference': photo_reference,
                            'maxwidth': 600,
                            'key': api_key
                        }
                        
                        return f"{photo_url}?{requests.compat.urlencode(photo_params)}"
                        
            return None
            
        except Exception as e:
            self.stdout.write(f"搜尋錯誤: {str(e)}")
            return None

    def download_and_save_photo(self, restaurant, photo_url):
        """下載並保存照片"""
        try:
            response = requests.get(photo_url, timeout=30)
            response.raise_for_status()
            
            # 清理檔案名稱
            safe_name = restaurant.name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            filename = f"{safe_name}.jpg"
            
            # 如果已有照片，先刪除舊檔案
            if restaurant.image:
                try:
                    if os.path.isfile(restaurant.image.path):
                        os.remove(restaurant.image.path)
                except:
                    pass
            
            # 保存新照片
            restaurant.image.save(
                filename,
                ContentFile(response.content),
                save=True
            )
            
            return True
            
        except Exception as e:
            self.stdout.write(f"下載失敗: {str(e)}")
            return False 