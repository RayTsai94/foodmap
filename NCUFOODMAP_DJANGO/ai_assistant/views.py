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
    """使用 Together API 獲取回應"""
    API_KEY = settings.TOGETHER_API_KEY
    logger.info(f"Using API KEY: {API_KEY[:5]}...")  # 只記錄前5個字符
    
    # 根據當前頁面定制提示詞
    page_contexts = {
        'home': """這是首頁，展示熱門餐廳和分類。
- 可以推薦最近好評的餐廳
- 可以解釋分類系統
- 可以指導如何使用搜尋功能
- 可以介紹網站主要功能""",

        'restaurant_list': """這是餐廳列表頁面。
- 可以解釋篩選條件的使用方法
- 可以說明排序選項的意義
- 可以建議如何找到特定類型的餐廳
- 可以解釋評分系統""",

        'restaurant_detail': "這是餐廳詳情頁面，提供餐廳的詳細資訊，包括菜單、評價、營業時間、位置等資訊，您也可以在這裡收藏餐廳。",
        'checkin': "這是打卡頁面，您可以記錄用餐體驗、上傳美食照片、分享心得，並查看其他人的打卡記錄。",
        'article': "這是文章留言板，您可以分享美食體驗、撰寫食記、與其他用戶互動討論。",
        'food_analysis': """這是食物分析頁面。
- 可以解釋各營養成分的意義
- 可以說明營養數據的來源
- 可以解釋健康建議的依據
- 必須提醒這是一般性建議，特殊情況需諮詢專業醫師
- 可以解釋如何解讀分析圖表""",
        'user_ranking': "這是用戶排行榜頁面，顯示活躍用戶、打卡王、評論達人等排名。",
        'restaurant_ranking': "這是餐廳排行榜頁面，展示最受歡迎、評分最高、打卡最多的餐廳排名。",
        'nutrition_dashboard': "這是營養儀表板頁面，提供個人飲食分析、營養攝入統計、飲食建議等資訊。",
        'dietary_preferences': "這是飲食偏好設置頁面，您可以設定個人飲食習慣、過敏原、特殊飲食需求等。",
        'allergen_info': "這是過敏原資訊頁面，提供食物過敏原查詢、安全飲食建議等資訊。",
        'ingredient_analysis': "這是食材分析頁面，提供食材的營養成分、熱量、健康效益等詳細資訊。",
        'ai_food_analysis': """這是AI食物分析頁面。
- 可以指導如何詳細描述食物以獲得更準確的分析
- 可以解釋營養成分的計算方式
- 可以說明數據的可信度
- 必須說明這是估算值，僅供參考
- 可以建議如何使用分析結果改善飲食""",
        'ai_advisor': """這是智能營養顧問頁面。
- 可以根據用戶提供的資訊給出個人化建議
- 必須說明建議的依據和限制
- 可以解釋如何追蹤營養目標
- 可以建議如何平衡營養攝入
- 必須提醒特殊情況需要專業醫療建議""",
        'user_profile': "這是個人資料頁面，您可以查看和編輯個人資訊、管理收藏的餐廳、查看活動歷史。",
        'favorite_restaurants': "這是收藏餐廳頁面，顯示您收藏的所有餐廳清單。",
        'user_checkins': "這是我的打卡頁面，記錄您的所有打卡歷史。",
        'user_articles': "這是我的文章頁面，顯示您發表的所有文章和評論。",
        'settings': "這是設定頁面，您可以調整帳號設定、隱私設定、通知偏好等。",
        'delete_account': "這是刪除帳號頁面，您可以刪除您的帳號。"
    }

    # 獲取頁面上下文，如果沒有特定頁面則使用通用上下文
    context = page_contexts.get(current_page, """這是NCU食物地圖網站，提供以下功能：
- 中央大學周邊餐廳資訊查詢
- 美食推薦和評分系統
- 營養成分分析
- 個人化飲食建議
- 用戶打卡和分享功能

我可以協助您：
1. 查找特定類型的餐廳
2. 了解食物的營養價值
3. 獲取健康飲食建議
4. 使用網站的各項功能""")
    
    system_prompt = """你是NCU食物地圖網站的AI助手。請注意以下要求：
1. 必須使用繁體中文回答
2. 禁止使用簡體中文
3. 回答要簡潔友善
4. 提供具體的操作建議
5. 回答要符合台灣的用語習慣
6. 數字優先使用半形
7. 標點符號使用全形"""

    user_prompt = f"""當前頁面情境：{context}

用戶問題：{message}

請根據頁面情境提供相關的具體建議和資訊。回答必須：
1. 符合當前頁面的功能和目的
2. 提供具體可行的操作步驟
3. 必要時加入相關的注意事項
4. 使用台灣的用語習慣"""

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
                "max_tokens": 800
            },
            timeout=30
        )
        
        logger.info(f"API Response status: {response.status_code}")
        logger.info(f"API Response content: {response.text[:500]}")  # 只記錄前500個字符
        
        if response.status_code == 200:
            response_data = response.json()
            # choices 是 API 返回的回答陣列：
            # - 通常包含一個或多個可能的回答
            # - 每個 choice 包含：
            #   - message: 包含實際的回答內容
            #   - finish_reason: 回答結束的原因（length/stop/content_filter等）
            #   - index: 如果有多個回答，這是回答的索引號
            if 'choices' in response_data and len(response_data['choices']) > 0:
                return response_data['choices'][0]['message']['content'].strip()
            else:
                logger.error(f"Unexpected API response structure: {response_data}")
                return "抱歉，AI 回應格式不正確。請稍後再試。"
        else:
            logger.error(f"API request failed with status {response.status_code}: {response.text}")
            return f"抱歉，API 請求失敗（狀態碼：{response.status_code}）。請稍後再試。"
    except requests.exceptions.Timeout:
        logger.error("API request timed out")
        return "抱歉，請求超時。請稍後再試。"
    except Exception as e:
        logger.error(f"Error in get_ai_response: {str(e)}", exc_info=True)
        return f"抱歉，發生錯誤：{str(e)}。請稍後再試。"

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
        # 獲取最近的5組對話
        history = ChatHistory.objects.filter(
            user=request.user if request.user.is_authenticated else None,
            session_id=request.session.session_key
        ).order_by('-created_at')[:10]  # 獲取最近的10條消息（5組對話）
        
        # 將查詢結果轉換為列表並反轉順序（讓最早的消息在前）
        messages = []
        for chat in reversed(list(history)):
            messages.append({
                'type': 'user',
                'content': chat.message
            })
            messages.append({
                'type': 'assistant',
                'content': chat.response
            })
            
        return JsonResponse({'messages': messages})
    except Exception as e:
        logger.error(f"Error in get_chat_history: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)
