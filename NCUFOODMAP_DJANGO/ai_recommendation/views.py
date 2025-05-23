from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse
from .models import AIRecommendation
from restaurants.models import Restaurant  # 引入餐廳模型
import together
import googlemaps
from django.views.decorators.csrf import csrf_exempt
import json
import logging
import traceback
import math

logger = logging.getLogger(__name__)

def index(request):
    return render(request, 'ai_recommendation/index.html', {
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY
    })

def calculate_distance(lat1, lng1, lat2, lng2):
    """計算兩點間距離（公里）"""
    # 使用 Haversine 公式
    R = 6371  # 地球半徑（公里）
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    
    return distance

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
            
            # 中央大學座標
            NCU_LAT = 24.9684
            NCU_LNG = 121.1955
            SEARCH_RADIUS_KM = 5  # 搜尋半徑5公里
            
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
                # 使用 Google Maps API 搜尋相關位置，限制在中央大學附近5公里
                gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
                
                # 搜尋店家，指定位置和半徑
                search_query = f"{ai_response['store_type']}"
                logger.info(f"Google Maps 搜尋查詢：{search_query}")
                
                # 使用 nearby_search 限制搜尋範圍
                places_result = gmaps.places_nearby(
                    location=(NCU_LAT, NCU_LNG),
                    radius=SEARCH_RADIUS_KM * 1000,  # 轉換為公尺
                    keyword=search_query,
                    type='restaurant'
                )
                
                if not places_result.get('results'):
                    # 如果沒有結果，嘗試文字搜尋
                    search_query_with_location = f"{ai_response['store_type']} 中央大學附近"
                    places_result = gmaps.places(search_query_with_location)
                
                if not places_result.get('results'):
                    return JsonResponse({
                        'success': False,
                        'error': '找不到符合條件的店家'
                    })
                
                recommendations = []
                processed_count = 0
                
                for place in places_result.get('results', []):
                    if processed_count >= 5:  # 限制最多5個結果
                        break
                        
                    location = place['geometry']['location']
                    place_lat = location['lat']
                    place_lng = location['lng']
                    
                    # 檢查是否在5公里範圍內
                    distance = calculate_distance(NCU_LAT, NCU_LNG, place_lat, place_lng)
                    if distance > SEARCH_RADIUS_KM:
                        continue
                    
                    # 獲取店家詳細資訊，包括評分和網站
                    place_details = gmaps.place(
                        place_id=place['place_id'],
                        fields=['name', 'formatted_address', 'rating', 'website']
                    )
                    
                    # 獲取照片URL（從nearby_search結果中）
                    photo_url = None
                    if place.get('photos') and len(place['photos']) > 0:
                        photo_reference = place['photos'][0]['photo_reference']
                        photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_reference}&key={settings.GOOGLE_MAPS_API_KEY}"
                    
                    # 檢查是否已存在於本地資料庫
                    existing_restaurant = Restaurant.objects.filter(
                        name=place['name'],
                        lat__isnull=False,
                        lng__isnull=False
                    ).first()
                    
                    local_image_url = None
                    if existing_restaurant and existing_restaurant.image:
                        local_image_url = existing_restaurant.image.url
                    
                    recommendation = AIRecommendation(
                        query=query,
                        store_type=ai_response['store_type'],
                        store_name=place['name'],
                        address=place.get('formatted_address', ''),
                        latitude=place_lat,
                        longitude=place_lng,
                        ai_analysis=ai_response['analysis']
                    )
                    recommendation.save()

                    recommendations.append({
                        'name': place['name'],
                        'address': place.get('formatted_address', ''),
                        'lat': place_lat,
                        'lng': place_lng,
                        'type': ai_response['store_type'],
                        'analysis': ai_response['analysis'],
                        'distance': round(distance, 2),
                        'rating': place_details.get('result', {}).get('rating', 0),
                        'photo_url': photo_url,
                        'local_image_url': local_image_url,
                        'website': place_details.get('result', {}).get('website', '')
                    })
                    
                    processed_count += 1
                
                if not recommendations:
                    return JsonResponse({
                        'success': False,
                        'error': '在中央大學附近5公里內找不到符合條件的餐廳'
                    })
                
                # 按距離排序
                recommendations.sort(key=lambda x: x['distance'])
                
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
