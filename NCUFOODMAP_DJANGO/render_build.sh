#!/usr/bin/env bash
# 創建媒體文件目錄
mkdir -p /opt/render/project/src/media/restaurant_images

# 設置目錄權限
chmod -R 755 /opt/render/project/src/media

# 安裝依賴
python -m pip install --upgrade pip
pip install -r requirements.txt

# 收集靜態文件
python manage.py collectstatic --noinput

# 運行數據庫遷移
python manage.py migrate 