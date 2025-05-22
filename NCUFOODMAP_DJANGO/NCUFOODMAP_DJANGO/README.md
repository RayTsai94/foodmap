# NCU 食物地圖

NCU 食物地圖是一個用於探索中央大學周邊餐廳的網站，結合了地圖功能和食物營養分析，幫助用戶了解餐廳菜單的營養資訊。

## 功能特點

- 餐廳列表與詳細資訊
- 整合 Google Maps 的互動地圖
- 菜單項目詳情與圖片展示 
- 營養分析儀表板
- 食材與過敏原資訊
- 飲食偏好推薦
- 用戶評論與評分系統

## 技術堆疊

- **後端框架**: Django 4.2
- **前端技術**: HTML, CSS, JavaScript, Bootstrap 5
- **資料庫**: SQLite (開發) / PostgreSQL (可選用於生產環境)
- **地圖整合**: Google Maps API
- **外部套件**: django-crispy-forms, django-cors-headers, djangorestframework

## 安裝指南

### 先決條件

- Python 3.8 或更高版本
- pip (Python 包管理器)

### 安裝步驟

1. 克隆存儲庫：
   ```
   git clone <儲存庫地址>
   cd ncufoodmap_django
   ```

2. 建立虛擬環境：
   ```
   python -m venv venv
   ```

3. 啟動虛擬環境：
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. 安裝相依套件：
   ```
   pip install -r requirements.txt
   ```

5. 進行資料庫遷移：
   ```
   python manage.py makemigrations
   python manage.py migrate
   ```

6. 創建超級用戶：
   ```
   python manage.py createsuperuser
   ```

7. 啟動開發伺服器：
   ```
   python manage.py runserver
   ```

8. 訪問以下 URL:
   - 網站首頁: http://127.0.0.1:8000/
   - 管理介面: http://127.0.0.1:8000/admin/

## 使用指南

1. 使用管理介面添加餐廳、菜單項目和分類
2. 透過首頁或餐廳列表頁面瀏覽餐廳
3. 查看地圖上的餐廳位置
4. 閱讀和撰寫餐廳評論
5. 探索菜單項目的營養資訊和成分

## API 金鑰設定

本專案需要以下 API 金鑰：

1. **Google Maps API 金鑰**：
   - 用於地圖功能
   - 在 settings.py 中已設置

2. **Together API 金鑰**：
   - 用於食物分析功能
   - 在 settings.py 中已設置

## 貢獻者

本專案由中央大學團隊開發，歡迎提交 Pull Requests 或建立 Issues 來改進專案。

## 授權條款

本專案採用 MIT 授權條款 - 詳見 LICENSE 文件 