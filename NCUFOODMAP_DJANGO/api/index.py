import os
import sys
from pathlib import Path

# 設置項目根目錄
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# 設置 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ncufoodmap_backend.vercel_settings')

try:
    import django
    django.setup()
    
    from django.core.wsgi import get_wsgi_application
    
    # 創建 Django 應用
    application = get_wsgi_application()
    
except Exception as e:
    # 如果設置失敗，創建錯誤處理器
    def application(environ, start_response):
        from django.http import HttpResponse
        response = HttpResponse(f"初始化錯誤: {str(e)}", status=500)
        status = '500 Internal Server Error'
        headers = [('Content-Type', 'text/html')]
        start_response(status, headers)
        return [response.content]

# Vercel 會自動處理 WSGI 應用
app = application 