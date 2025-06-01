from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
import json
import requests
import logging
from .models import ChatHistory

# 設置日誌
logger = logging.getLogger(__name__)

def get_ai_response(message, current_page):
    """AI助手：網站導覽與功能介紹，遇到健康/營養/飲食/疾病問題時引導，其他問題呼叫Together AI生成說明。"""
    API_KEY = settings.TOGETHER_API_KEY
    logger.info(f"Using API KEY: {API_KEY[:5]}...")

    # 健康/營養/飲食/疾病關鍵字
    health_keywords = [
        "減肥", "減重", "瘦身", "減脂", "體重", "蛋白質", "營養", "維生素", "礦物質", "膳食纖維", "碳水化合物", "脂肪", "熱量", "卡路里", "素食", "糖尿病", "高血壓", "高血脂", "心臟病", "腎臟病", "肝臟病", "痛風", "過敏", "飲食", "健康", "疾病", "飲食原則", "飲食建議", "健康建議"
    ]
    if any(keyword in message for keyword in health_keywords):
        return "您好，關於健康、營養、飲食相關的問題，建議您使用『AI食物營養分析』功能進行食物成分分析，或查看『個人飲食日記』和『營養儀表板』來追蹤您的飲食狀況。本 AI 助手主要提供網站導覽與功能說明。"

    # 詳細的頁面功能說明
    page_details = {
        "home": {
            "name": "首頁",
            "intro": "歡迎來到 NCU 食物地圖！這裡是您探索中央大學美食世界的起點。",
            "features": [
                "🏠 瀏覽網站主要功能概覽",
                "🍽️ 快速進入餐廳地圖、營養分析等核心功能",
                "📰 查看最新美食文章與校園飲食資訊",
                "👥 訪問社交功能，與同學分享美食經驗",
                "🎯 使用快速導航前往各個功能頁面"
            ],
            "how_to": "點擊導航欄或首頁卡片即可進入相應功能。建議先從地圖功能開始探索附近餐廳！"
        },
        "map": {
            "name": "餐廳地圖",
            "intro": "探索中央大學周邊的所有美食選擇！互動式地圖讓您輕鬆找到心儀的餐廳。",
            "features": [
                "🗺️ 互動式地圖顯示所有餐廳位置",
                "🔍 搜尋特定餐廳或美食類型",
                "📍 點擊地圖標記查看餐廳詳細資訊",
                "⭐ 查看其他用戶的評價與評分",
                "📱 獲取餐廳聯絡方式與營業時間",
                "🚶 查看從您當前位置到餐廳的路線"
            ],
            "how_to": "在地圖上點擊紅色標記查看餐廳詳情，使用左上角搜尋框快速找到特定餐廳，或使用篩選功能按照評分、距離等條件篩選。"
        },
        "restaurant_list": {
            "name": "餐廳列表",
            "intro": "以清單形式瀏覽所有餐廳，方便比較和篩選。",
            "features": [
                "📋 完整的餐廳清單檢視",
                "🔽 按名稱、評分、距離等排序",
                "🏷️ 按料理類型、價位等篩選",
                "⭐ 快速查看評分與評論摘要",
                "🔗 點擊進入餐廳詳細頁面"
            ],
            "how_to": "使用頁面頂部的排序和篩選選項找到符合需求的餐廳，點擊餐廳名稱查看詳細資訊。"
        },
        "restaurant_detail": {
            "name": "餐廳詳情",
            "intro": "深入了解特定餐廳的所有資訊。",
            "features": [
                "🏪 餐廳基本資訊（地址、電話、營業時間）",
                "🍜 完整菜單與價格",
                "📸 餐廳與料理照片",
                "💬 用戶評論與評分",
                "🗺️ 位置地圖與交通資訊"
            ],
            "how_to": "瀏覽餐廳資訊，查看菜單選擇餐點，閱讀其他用戶評論幫助決策。"
        },
        "ai_food_analysis": {
            "name": "AI食物營養分析",
            "intro": "運用AI技術分析食物營養成分，幫助您了解每一餐的營養價值。",
            "features": [
                "🔍 輸入食物名稱進行營養分析",
                "📊 生成詳細營養成分圖表",
                "🥗 獲得營養價值評估",
                "💡 收到個人化營養建議",
                "📋 保存分析記錄到個人日記"
            ],
            "how_to": "在輸入框中描述您要分析的食物（如：麻婆豆腐飯），點擊分析按鈕，AI會為您生成營養報告和建議。"
        },
        "ai_nutrition_consultant": {
            "name": "AI營養顧問",
            "intro": "您的專屬AI營養師！提供專業的營養諮詢與健康飲食建議，支援即時對話互動。",
            "features": [
                "🩺 專業營養師級別的健康諮詢",
                "💬 即時對話式互動體驗",
                "🎯 個人化減肥、增肌、疾病調理建議",
                "🏃‍♂️ 運動營養與健身飲食指導",
                "📚 基於科學依據的營養知識分享",
                "⚡ 快速回應各種營養健康問題"
            ],
            "how_to": "直接在聊天框中輸入您的問題，如：'我想減肥該怎麼吃？'或點擊建議問題按鈕快速開始對話。AI營養師會根據您的情況提供專業建議。"
        },
        "personal_food_diary": {
            "name": "個人飲食日記",
            "intro": "記錄與追蹤您的每日飲食，建立健康的飲食習慣。",
            "features": [
                "📝 記錄每日餐食內容",
                "📊 查看營養攝取統計",
                "📅 按日期瀏覽飲食歷史",
                "🎯 設定個人營養目標",
                "📈 追蹤飲食改善進度"
            ],
            "how_to": "點擊'新增記錄'按鈕，輸入今天吃的食物，系統會自動計算營養成分並加入您的飲食日記。"
        },
        "personal_nutrition_dashboard": {
            "name": "個人營養儀表板",
            "intro": "一目了然您的營養狀況，協助達成健康目標。",
            "features": [
                "📊 營養攝取視覺化圖表",
                "🎯 目標達成度追蹤",
                "📈 週/月營養趨勢分析",
                "⚡ 營養攝取建議提醒",
                "🏆 健康里程碑記錄"
            ],
            "how_to": "查看圖表了解營養攝取狀況，點擊各個指標獲得詳細說明，根據建議調整飲食習慣。"
        },
        "ai_recommendation": {
            "name": "AI美食推薦",
            "intro": "基於您的偏好與需求，AI為您推薦最適合的餐廳與餐點。",
            "features": [
                "🤖 個人化餐廳推薦",
                "🍽️ 根據營養需求推薦餐點",
                "🎯 考量預算與距離的智能推薦",
                "⭐ 結合評價的優質推薦",
                "🔄 持續學習您的偏好"
            ],
            "how_to": "填寫您的偏好（料理類型、預算、距離等），AI會為您推薦最合適的選擇。越多互動，推薦越精準！"
        },
        "checkin_list": {
            "name": "打卡記錄",
            "intro": "記錄您的美食足跡，與朋友分享用餐體驗。",
            "features": [
                "📍 餐廳打卡記錄",
                "⭐ 為餐廳評分與評論",
                "📸 分享用餐照片",
                "🏆 查看個人打卡統計",
                "👥 瀏覽朋友的用餐動態"
            ],
            "how_to": "在餐廳用餐時點擊打卡按鈕，為餐廳評分並分享您的用餐感受。"
        },
        "article_list": {
            "name": "美食文章",
            "intro": "探索豐富的美食文章，獲得飲食靈感與知識。",
            "features": [
                "📰 閱讀最新美食文章",
                "✍️ 發表個人美食心得",
                "💬 與其他用戶交流討論",
                "🔖 收藏喜愛的文章",
                "🔍 搜尋特定主題文章"
            ],
            "how_to": "瀏覽文章列表，點擊標題閱讀全文，登入後可發表評論或撰寫自己的美食文章。"
        },
        "social": {
            "name": "社交功能",
            "intro": "與同學朋友分享美食體驗，建立美食社群。",
            "features": [
                "👥 添加好友與關注",
                "💬 私訊與群組聊天",
                "📱 分享用餐動態",
                "🎉 參加美食活動",
                "🏆 查看排行榜與成就"
            ],
            "how_to": "搜尋並添加朋友，分享您的用餐體驗，參與社群討論，一起探索校園美食！"
        }
    }

    # 獲取當前頁面的詳細資訊
    page_info = page_details.get(current_page)
    if not page_info:
        # 預設回應
        intro = "這是 NCU 食物地圖網站，您可以查詢校園附近美食、營養資訊與健康建議。如需網站操作說明，歡迎隨時詢問！"
    else:
        intro = f"您目前在【{page_info['name']}】\n\n{page_info['intro']}\n\n主要功能：\n" + "\n".join(page_info['features']) + f"\n\n使用方式：{page_info['how_to']}"

    # 組合 prompt
    system_prompt = f"""你是 NCU 食物地圖網站的 AI 助手，只負責網站導覽與功能介紹。請根據用戶所在的頁面詳細說明該頁面的用途、主要功能、操作方式。遇到健康、營養、飲食、疾病等問題時，請禮貌地建議用戶前往『智能營養顧問』頁面詢問。

當前頁面資訊：{intro}

請用繁體中文回答，語氣親切友好。如果用戶詢問其他頁面功能，可以簡單介紹並建議前往該頁面使用。"""
    
    user_prompt = f"用戶在【{page_info['name'] if page_info else current_page}】頁面提問：{message}"

    # 呼叫 Together AI 生成網站導覽說明
    try:
        logger.info(f"Sending request to Together API with prompt: {user_prompt}")
        response = requests.post(
            "https://api.together.xyz/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 500
            },
            timeout=30
        )
        logger.info(f"API Response status: {response.status_code}")
        logger.info(f"API Response content: {response.text[:500]}")
        if response.status_code == 200:
            response_data = response.json()
            if 'choices' in response_data and len(response_data['choices']) > 0:
                return response_data['choices'][0]['message']['content'].strip()
            else:
                logger.error(f"Unexpected API response structure: {response_data}")
                return intro
        else:
            logger.error(f"API request failed with status {response.status_code}: {response.text}")
            return intro
    except Exception as e:
        logger.error(f"Error in get_ai_response: {str(e)}", exc_info=True)
        return intro

@csrf_exempt
@require_POST
def chat(request):
    """處理聊天請求"""
    try:
        data = json.loads(request.body)
        message = data.get('message')
        current_page = data.get('current_page', '')
        
        logger.info(f"Received chat request - Message: {message}, Page: {current_page}")
        
        if not message:
            return JsonResponse({'error': '請輸入訊息'}, status=400)
        
        # 獲取AI回應
        response = get_ai_response(message, current_page)
        
        # 保存對話歷史
        ChatHistory.objects.create(
            user=request.user if request.user.is_authenticated else None,
            session_id=request.session.session_key or '',
            message=message,
            response=response,
            current_page=current_page
        )
        
        return JsonResponse({'response': response})
    except Exception as e:
        logger.error(f"Error in chat view: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

@require_GET
def get_chat_history(request):
    """獲取用戶的聊天歷史記錄"""
    try:
        # 獲取最近的10組對話
        history = ChatHistory.objects.filter(
            user=request.user if request.user.is_authenticated else None,
            session_id=request.session.session_key
        ).order_by('-created_at')[:10]  # 獲取最近的10條消息
        
        # 將查詢結果轉換為列表並反轉順序（讓最早的消息在前）
        messages = []
        for chat in reversed(list(history)):
            messages.append({
                'type': 'user',
                'content': chat.message,
                'timestamp': chat.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
            messages.append({
                'type': 'assistant',
                'content': chat.response,
                'timestamp': chat.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
            
        return JsonResponse({'messages': messages})
    except Exception as e:
        logger.error(f"Error in get_chat_history: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)
