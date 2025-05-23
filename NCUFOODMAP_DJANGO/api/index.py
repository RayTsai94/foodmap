from django.http import HttpResponse
import os
import sys

# 添加項目根目錄到 Python 路徑
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 設置 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ncufoodmap_backend.vercel_settings')

import django
django.setup()

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

def handler(request):
    """簡單的測試處理器"""
    return HttpResponse("Hello from NCU Food Map Django App on Vercel!") 