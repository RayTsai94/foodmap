from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse
from .models import AIRecommendation
import together
import googlemaps
from django.views.decorators.csrf import csrf_exempt
import json
import logging
import traceback

logger = logging.getLogger(__name__)

def index(request):
    return render(request, 'ai_recommendation/index.html', {
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY
    })

@csrf_exempt
def get_recommendation(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            query = data.get('query', '')
            
            if not query:
                return JsonResponse({
                    'success': False,
                    'error': '請輸入搜尋內容'
                })
            
            # 設定 Together AI API
            together.api_key = settings.TOGETHER_API_KEY
            
            # 使用 Together AI 進行分析
            prompt = f"""你是一個專業的餐廳推薦助手。請根據以下需求，分析並推薦合適的餐廳類型：

查詢需求: {query}

請以JSON格式回答，格式如下：
{{
    "store_type": "餐廳類型（例如：日式料理、咖啡廳等）",
    "analysis": "詳細分析這類型餐廳為什麼適合該需求"
}}

請確保回應是有效的JSON格式。"""
            
            try:
                logger.info(f"發送請求到 Together AI，查詢：{query}")
                
                output = together.Complete.create(
                    prompt=prompt,
                    model="mistralai/Mixtral-8x7B-Instruct-v0.1",
                    max_tokens=1000,
                    temperature=0.7,
                    top_k=50,
                    top_p=0.7,
                    repetition_penalty=1.1
                )
                
                logger.info(f"Together AI 回應：{output}")
                
                # 直接獲取回應文本
                response_text = output['choices'][0]['text']
                # 清理回應文本，確保它是有效的 JSON
                response_text = response_text.strip()
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()
                
                logger.info(f"清理後的回應文本：{response_text}")
                
                try:
                    ai_response = json.loads(response_text)
                except json.JSONDecodeError as je:
                    logger.error(f"JSON 解析錯誤：{str(je)}")
                    logger.error(f"問題文本：{response_text}")
                    return JsonResponse({
                        'success': False,
                        'error': 'AI 回應格式錯誤，請重試'
                    })
                
                if not isinstance(ai_response, dict) or 'store_type' not in ai_response or 'analysis' not in ai_response:
                    logger.error(f"AI 回應格式不正確：{ai_response}")
                    return JsonResponse({
                        'success': False,
                        'error': 'AI 回應格式不完整，請重試'
                    })
                
            except Exception as e:
                logger.error(f"Together AI API 錯誤：{str(e)}")
                logger.error(f"錯誤詳情：{traceback.format_exc()}")
                return JsonResponse({
                    'success': False,
                    'error': f'AI 分析過程中發生錯誤：{str(e)}'
                })
            
            try:
                # 使用 Google Maps API 搜尋相關位置
                gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
                
                # 搜尋店家
                search_query = f"{ai_response['store_type']} near NCU"
                logger.info(f"Google Maps 搜尋查詢：{search_query}")
                
                places_result = gmaps.places(search_query)
                
                if not places_result.get('results'):
                    return JsonResponse({
                        'success': False,
                        'error': '找不到符合條件的店家'
                    })
                
                recommendations = []
                
                for place in places_result.get('results', [])[:3]:  # 取前3個結果
                    location = place['geometry']['location']
                    
                    recommendation = AIRecommendation(
                        query=query,
                        store_type=ai_response['store_type'],
                        store_name=place['name'],
                        address=place.get('formatted_address', ''),
                        latitude=location['lat'],
                        longitude=location['lng'],
                        ai_analysis=ai_response['analysis']
                    )
                    recommendation.save()

                    recommendations.append({
                        'name': place['name'],
                        'address': place.get('formatted_address', ''),
                        'lat': location['lat'],
                        'lng': location['lng'],
                        'type': ai_response['store_type'],
                        'analysis': ai_response['analysis']
                    })
                
                return JsonResponse({
                    'success': True,
                    'recommendations': recommendations
                })
                
            except Exception as e:
                logger.error(f"Google Maps API 錯誤：{str(e)}")
                logger.error(f"錯誤詳情：{traceback.format_exc()}")
                return JsonResponse({
                    'success': False,
                    'error': '搜尋位置時發生錯誤，請稍後再試'
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': '無效的請求格式'
            })
        except Exception as e:
            logger.error(f"未預期的錯誤：{str(e)}")
            logger.error(f"錯誤詳情：{traceback.format_exc()}")
            return JsonResponse({
                'success': False,
                'error': '發生未預期的錯誤，請稍後再試'
            })
    
    return JsonResponse({
        'success': False,
        'error': '不支援的請求方法'
    })
