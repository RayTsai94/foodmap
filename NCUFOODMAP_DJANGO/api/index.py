import os
import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# 設置 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ncufoodmap_backend.vercel_settings')

try:
    import django
    django.setup()
    
    from django.core.wsgi import get_wsgi_application
    from django.http import HttpResponse
    
    # 創建 WSGI 應用
    application = get_wsgi_application()
    
    # 這個函數是 Vercel 的入口點
    def handler(request):
        """Vercel 處理函數"""
        return application(request.environ, lambda status, headers: None)
        
except Exception as e:
    # 如果 Django 設置失敗，返回錯誤信息
    def handler(request):
        from django.http import HttpResponse
        return HttpResponse(f"Django setup error: {str(e)}", status=500) 