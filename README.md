# 🍽️ Food Map 中大美食打卡校園社交互動平台

## 專案主題
《Food Map 中大美食打卡校園社交互動平台》

## 組員名單
吳辰夜、蔡睿中、李昭儀、葉治廷、游旻峻

---

## 網站介紹

Food Map 是一款結合趣味、美食探索與社交互動的中央大學校園地圖式社交網站。使用者可以透過地圖輕鬆紀錄與分享自己在校園內外發現的美食，並藉由 AI 分析提供個人化的飲食推薦與熱度地圖，打造出既實用又有趣的美食社群互動平台。

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

## 網站目的

現代學生生活忙碌，尋找美食成為調劑壓力的重要方式。本平台希望解決以下問題：
- 美食資訊零散，缺乏即時分享與互動社群。
- 希望有更直覺且趣味的方式記錄、探索校園周邊美食。
- 透過地圖可視化與健康推薦，提升飲食體驗與身體意識。

## 目標用戶
- 中央大學在校學生、教職員
- 熱愛探索校園周邊美食的人
- 喜歡分享打卡、體驗不同餐廳與小吃的人
- 注重飲食健康，想了解飲食習慣者
- 喜歡有趣互動、地圖式社交的年輕族群

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
