import requests
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = '測試 Google Places API Key 是否有效'

    def add_arguments(self, parser):
        parser.add_argument(
            '--api-key',
            type=str,
            help='Google Places API Key',
            required=True
        )

    def handle(self, *args, **options):
        api_key = options['api_key']
        
        # 測試 API key 格式
        self.stdout.write(f'API Key: {api_key}')
        self.stdout.write(f'API Key 長度: {len(api_key)}')
        
        # 測試簡單的 Place Search
        test_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        test_params = {
            'query': '麥當勞',
            'key': api_key
        }
        
        try:
            self.stdout.write('正在測試 API 請求...')
            response = requests.get(test_url, params=test_params, timeout=10)
            
            self.stdout.write(f'HTTP 狀態碼: {response.status_code}')
            
            if response.status_code == 200:
                data = response.json()
                self.stdout.write(f'API 回應狀態: {data.get("status", "未知")}')
                
                if data.get('status') == 'OK':
                    results = data.get('results', [])
                    self.stdout.write(self.style.SUCCESS(f'✓ API 正常！找到 {len(results)} 個結果'))
                    if results:
                        first_result = results[0]
                        self.stdout.write(f'第一個結果: {first_result.get("name", "未知名稱")}')
                        
                        # 測試照片
                        if 'photos' in first_result:
                            self.stdout.write('✓ 該地點有照片可用')
                        else:
                            self.stdout.write('⚠ 該地點沒有照片')
                else:
                    self.stdout.write(
                        self.style.ERROR(f'✗ API 錯誤: {data.get("status")} - {data.get("error_message", "未知錯誤")}')
                    )
            else:
                self.stdout.write(
                    self.style.ERROR(f'✗ HTTP 錯誤: {response.status_code}')
                )
                self.stdout.write(f'回應內容: {response.text[:500]}')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ 請求錯誤: {str(e)}')
            ) 