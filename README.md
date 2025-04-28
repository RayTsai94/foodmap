# 🍽️ Food Map 中大美食打卡校園社交互動平台

## 專案主題
《Food Map 中大美食打卡校園社交互動平台》

## 組員名單
吳辰夜、蔡睿中、李昭儀、葉治廷、游旻峻

---

## 網站介紹

Food Map 是一款結合趣味、美食探索與社交互動的中央大學校園地圖式社交網站。使用者可以透過地圖輕鬆紀錄與分享自己在校園內外發現的美食，並藉由 AI 分析提供個人化的飲食推薦與熱度地圖，打造出既實用又有趣的美食社群互動平台。

---

## 網站目的

現代學生生活忙碌，尋找美食成為調劑壓力的重要方式。本平台希望解決以下問題：
- 美食資訊零散，缺乏即時分享與互動社群。
- 希望有更直覺且趣味的方式記錄、探索校園周邊美食。
- 透過地圖可視化與健康推薦，提升飲食體驗與身體意識。

---

## 目標用戶
- 中央大學在校學生、教職員
- 熱愛探索校園周邊美食的人
- 喜歡分享打卡、體驗不同餐廳與小吃的人
- 注重飲食健康，想了解飲食習慣者
- 喜歡有趣互動、地圖式社交的年輕族群

---

## 功能細項
- **地圖定位功能**：使用 Google Maps API，標記美食地點
- **登入/註冊系統**：表單驗證 + JWT 安全認證
- **美食打卡紀錄**：地點、餐點名稱、照片上傳、心情、評分
- **AI 美食推薦**：根據打卡文字與評分，推薦相似餐廳或健康建議
- **自訂化打卡標記**：可愛圖示／顏色分類（甜點、正餐、飲料）
- **數據視覺化**：個人美食地圖、最多打卡時段、地圖熱度圖
- **社交功能**：加好友、留言、分享今日最推美食
- **可選功能**：美食心得評比排行榜、打卡成就徽章

---

## 技術架構
- 前端：React / Vite, Tailwind CSS, Google Maps JS API
- 後端：Node.js + Express, JWT, RESTful API
- 資料庫：MongoDB Atlas
- AI 分析：OpenAI GPT API（文字摘要推薦系統）
- 視覺圖表：Chart.js / Recharts
- 部署：Vercel（前端）、Render（後端）

---

## 團隊分工
| 組員 | 職位 | 技術 | 任務內容 |
|------|------|------|----------|
| 游旻峻 | 前端主管 (UI/UX 前端設計＋頁面製作) | React, Tailwind CSS, UI flow, Figma | 設計整體 UI 架構、繪製 Wireframe、實作頁與共用元件、定義元件命名與樣式 |
| 李昭儀 | 前端開發者 (登入＋使用者系統) | React Hook Form, Yup, JWT, 前端 API | 實作登入/註冊頁面、Token 儲存、登入後導頁邏輯、使用者個人頁資料顯示 |
| 吳辰夜 | 地圖互動設計師 (地圖功能＋美食記錄) | Google Maps JS API, Marker 操作, Axios, MongoDB | 實作地圖定位、打卡標記、美食資訊送至後端、顯示歷史紀錄 |
| 蔡睿中 | 後端工程師 (後端開發＋資料串接) | Node.js, Express, MongoDB, JWT, RESTful API | 撰寫登入、註冊、美食紀錄 API，處理 Token 驗證、資料存取與查詢 |
| 葉治廷 | AI 分析設計師 (AI 提問分析＋整合測試) | OpenAI API, Prompt 設計, Chart.js, Postman | 根據美食紀錄文字內容串接 GPT API，生成飲食建議、做統計圖表、協助測試與技術文件 |

---

## 架構圖

```
User
  │
  ▼
Google Maps
  │ Request
  ▼
Backend (Node.js Express)
  │ Responses
  ▼
Database (MongoDB Atlas)
  ▲
  │ Requests
Frontend (React/Vite)
  ▲
  │ Data
AI Analysis (OpenAI GPT)
  │ Dietary Advice
  ▼
Frontend (React/Vite)
```

---

## 授權 License

本專案採用 MIT 授權條款，詳情請見 [`LICENSE`](LICENSE)。
