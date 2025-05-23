import os
import sys
from pathlib import Path

# 設置 Django 專案路徑
DJANGO_DIR = Path(__file__).resolve().parent.parent / "NCUFOODMAP_DJANGO"
sys.path.insert(0, str(DJANGO_DIR))

# 設置 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ncufoodmap_backend.vercel_settings')

try:
    # 切換到 Django 目錄
    os.chdir(str(DJANGO_DIR))
    
    import django
    django.setup()
    
    from django.core.wsgi import get_wsgi_application
    
    # 創建 Django 應用
    application = get_wsgi_application()
    
except Exception as e:
    # 如果設置失敗，創建錯誤處理器
    def application(environ, start_response):
        status = '500 Internal Server Error'
        headers = [('Content-Type', 'text/html')]
        start_response(status, headers)
        error_msg = f"Django 初始化錯誤: {str(e)}\n路徑: {str(DJANGO_DIR)}\nPython 路徑: {sys.path[:3]}"
        return [error_msg.encode('utf-8')]

# Vercel 會自動處理 WSGI 應用
app = application 