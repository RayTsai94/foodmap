#!/usr/bin/env bash

# 創建 media 資料夾（給使用者上傳用）
mkdir -p /opt/render/project/src/media
chmod -R 755 /opt/render/project/src/media

# 安裝依賴
python -m pip install --upgrade pip
pip install -r requirements.txt

# 收集靜態檔案
python manage.py collectstatic --noinput

# 執行遷移
python manage.py migrate
