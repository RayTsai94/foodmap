#!/usr/bin/env python
"""
Vercel 數據初始化腳本 - 精簡版
"""
import os
import django
from django.conf import settings

def migrate_database():
    """執行基本的數據庫遷移"""
    try:
        # 確保 Django 已設置
        if not settings.configured:
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ncufoodmap_backend.vercel_settings')
            django.setup()
        
        # 執行數據庫遷移
        from django.core.management import call_command
        call_command('migrate', verbosity=0, interactive=False, run_syncdb=True)
        
        # 創建基本分類
        init_basic_data()
        
        print("✅ Vercel 數據庫初始化成功")
        
    except Exception as e:
        print(f"⚠️ 數據庫初始化警告: {e}")
        # 不拋出異常，允許應用繼續運行

def init_basic_data():
    """初始化基本數據"""
    try:
        from restaurants.models import Category
        
        # 只創建最基本的分類
        basic_categories = [
            {'name': '餐廳', 'icon': 'fas fa-utensils'},
            {'name': '飲料', 'icon': 'fas fa-coffee'},
            {'name': '小吃', 'icon': 'fas fa-shopping-bag'},
        ]
        
        for cat_data in basic_categories:
            Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'icon': cat_data['icon']}
            )
            
    except Exception as e:
        print(f"⚠️ 基本數據初始化警告: {e}")

if __name__ == '__main__':
    migrate_database() 