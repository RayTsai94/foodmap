from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Avg, Sum
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from restaurants.models import MenuItem, Restaurant
from .models import NutritionInfo, Ingredient, FoodPreference, PersonalFoodRecord, PersonalNutritionSummary
from .forms import FoodAnalysisForm, PersonalFoodRecordForm
import random
import os
import json
import together
from dotenv import load_dotenv
from django.conf import settings
import re
from django.http import JsonResponse
import requests

# 載入環境變數
load_dotenv()

# 初始化 Together AI 客戶端
together.api_key = settings.TOGETHER_API_KEY

def nutrition_dashboard(request):
    """營養分析儀表板，提供整體食品營養概覽"""
    # 獲取所有有營養信息的菜單項
    menu_items_with_nutrition = MenuItem.objects.filter(nutrition__isnull=False)
    
    # 計算平均營養值
    avg_nutrition = NutritionInfo.objects.aggregate(
        avg_calories=Avg('calories'),
        avg_protein=Avg('protein'),
        avg_carbs=Avg('carbs'),
        avg_fat=Avg('fat'),
        avg_fiber=Avg('fiber'),
        avg_sugar=Avg('sugar'),
        avg_sodium=Avg('sodium')
    )
    
    # 獲取低熱量（健康）選擇
    healthy_choices = MenuItem.objects.filter(
        nutrition__calories__lt=500,
        is_available=True
    ).order_by('nutrition__calories')[:6]
    
    # 獲取高蛋白選擇
    high_protein_choices = MenuItem.objects.filter(
        nutrition__protein__gte=20,
        is_available=True
    ).order_by('-nutrition__protein')[:6]
    
    # 按餐廳分組的營養信息
    restaurant_nutrition = Restaurant.objects.filter(
        menu_items__nutrition__isnull=False
    ).distinct().annotate(
        avg_calories=Avg('menu_items__nutrition__calories'),
        avg_protein=Avg('menu_items__nutrition__protein'),
        menu_count=Count('menu_items')
    ).order_by('avg_calories')
    
    # 營養分布統計
    nutrition_stats = {
        'low_calorie_count': MenuItem.objects.filter(nutrition__calories__lt=300, is_available=True).count(),
        'medium_calorie_count': MenuItem.objects.filter(nutrition__calories__gte=300, nutrition__calories__lt=600, is_available=True).count(),
        'high_calorie_count': MenuItem.objects.filter(nutrition__calories__gte=600, is_available=True).count(),
        'high_protein_count': MenuItem.objects.filter(nutrition__protein__gte=20, is_available=True).count(),
        'low_fat_count': MenuItem.objects.filter(nutrition__fat__lt=10, is_available=True).count(),
        'total_items': MenuItem.objects.filter(nutrition__isnull=False, is_available=True).count()
    }
    
    # 每日營養建議值（成人標準）
    daily_recommendations = {
        'calories': 2000,
        'protein': 50,
        'carbs': 300,
        'fat': 65,
        'fiber': 25,
        'sugar': 50,
        'sodium': 2300
    }
    
    return render(request, 'food_analysis/dashboard.html', {
        'avg_nutrition': avg_nutrition,
        'healthy_choices': healthy_choices,
        'high_protein_choices': high_protein_choices,
        'restaurant_nutrition': restaurant_nutrition,
        'nutrition_stats': nutrition_stats,
        'daily_recommendations': daily_recommendations,
    })

def dietary_preferences(request):
    """飲食偏好分析，顯示符合不同飲食偏好的選擇"""
    # 獲取所有飲食偏好類型
    diet_preferences = FoodPreference.objects.filter(type='DIET')
    
    # 為每個偏好獲取兼容的菜單項
    preferences_with_items = []
    for pref in diet_preferences:
        compatible_items = MenuItem.objects.filter(
            preferences__preference=pref,
            preferences__is_compatible=True,
            is_available=True
        )
        
        if compatible_items.exists():
            # 計算平均營養值
            avg_nutrition = compatible_items.aggregate(
                avg_calories=Avg('nutrition__calories'),
                avg_protein=Avg('nutrition__protein'),
                avg_carbs=Avg('nutrition__carbs'),
                avg_fat=Avg('nutrition__fat')
            )
            
            preferences_with_items.append({
                'preference': pref,
                'items': compatible_items[:6],  # 顯示前6項
                'total_count': compatible_items.count(),
                'avg_nutrition': avg_nutrition,
                'restaurants_count': compatible_items.values('restaurant').distinct().count()
            })
    
    # 飲食偏好統計
    preference_stats = {
        'vegetarian_count': MenuItem.objects.filter(
            preferences__preference__name__icontains='素食',
            preferences__is_compatible=True,
            is_available=True
        ).count(),
        'vegan_count': MenuItem.objects.filter(
            preferences__preference__name__icontains='全素',
            preferences__is_compatible=True,
            is_available=True
        ).count(),
        'gluten_free_count': MenuItem.objects.filter(
            preferences__preference__name__icontains='無麩質',
            preferences__is_compatible=True,
            is_available=True
        ).count(),
        'low_carb_count': MenuItem.objects.filter(
            nutrition__carbs__lt=20,
            is_available=True
        ).count()
    }
    
    return render(request, 'food_analysis/dietary_preferences.html', {
        'preferences_with_items': preferences_with_items,
        'preference_stats': preference_stats,
    })

def allergen_info(request):
    """過敏原信息頁面，顯示常見過敏原和不含這些過敏原的菜單項"""
    # 獲取所有過敏原偏好
    allergens = FoodPreference.objects.filter(type='ALLERGY')
    
    # 為每個過敏原獲取不兼容的菜單項（即不含該過敏原的菜單）
    allergen_free_items = []
    for allergen in allergens:
        free_items = MenuItem.objects.filter(
            preferences__preference=allergen,
            preferences__is_compatible=False,
            is_available=True
        )
        
        if free_items.exists():
            # 計算安全選擇的營養統計
            avg_nutrition = free_items.aggregate(
                avg_calories=Avg('nutrition__calories'),
                avg_protein=Avg('nutrition__protein')
            )
            
            allergen_free_items.append({
                'allergen': allergen,
                'items': free_items[:6],
                'total_count': free_items.count(),
                'avg_nutrition': avg_nutrition,
                'restaurants_count': free_items.values('restaurant').distinct().count()
            })
    
    # 過敏原統計
    allergen_stats = {
        'gluten_free_count': MenuItem.objects.filter(
            preferences__preference__name__icontains='麩質',
            preferences__is_compatible=False,
            is_available=True
        ).count(),
        'dairy_free_count': MenuItem.objects.filter(
            preferences__preference__name__icontains='乳製品',
            preferences__is_compatible=False,
            is_available=True
        ).count(),
        'nut_free_count': MenuItem.objects.filter(
            preferences__preference__name__icontains='堅果',
            preferences__is_compatible=False,
            is_available=True
        ).count(),
        'seafood_free_count': MenuItem.objects.filter(
            preferences__preference__name__icontains='海鮮',
            preferences__is_compatible=False,
            is_available=True
        ).count(),
        'total_safe_items': MenuItem.objects.filter(
            preferences__preference__type='ALLERGY',
            preferences__is_compatible=False,
            is_available=True
        ).distinct().count()
    }
    
    # 常見過敏原資訊
    common_allergens = [
        {
            'name': '麩質 (小麥)',
            'description': '存在於小麥、大麥、黑麥等穀物中',
            'symptoms': '腹痛、腹瀉、皮疹、疲勞',
            'avoid_foods': '麵包、麵條、啤酒、醬油',
            'safe_alternatives': '米飯、玉米、藜麥、無麩質產品'
        },
        {
            'name': '乳製品',
            'description': '包含牛奶蛋白或乳糖',
            'symptoms': '腹脹、腹瀉、皮疹、呼吸困難',
            'avoid_foods': '牛奶、起司、奶油、優格',
            'safe_alternatives': '豆漿、杏仁奶、椰奶、燕麥奶'
        },
        {
            'name': '堅果',
            'description': '包括樹堅果和花生',
            'symptoms': '蕁麻疹、腫脹、呼吸困難、過敏性休克',
            'avoid_foods': '花生、杏仁、核桃、腰果',
            'safe_alternatives': '葵花籽、南瓜籽、椰子'
        },
        {
            'name': '海鮮',
            'description': '魚類、貝類、甲殼類',
            'symptoms': '皮疹、腫脹、噁心、呼吸困難',
            'avoid_foods': '魚、蝦、蟹、貝類',
            'safe_alternatives': '雞肉、豬肉、豆腐、蛋類'
        }
    ]
    
    return render(request, 'food_analysis/allergen_info.html', {
        'allergen_free_items': allergen_free_items,
        'allergen_stats': allergen_stats,
        'common_allergens': common_allergens,
    })

def ingredient_analysis(request):
    """食材分析頁面，顯示不同食材的使用情況"""
    # 獲取使用最多的前10種食材
    top_ingredients = Ingredient.objects.annotate(
        usage_count=Count('menu_items')
    ).order_by('-usage_count')[:10]
    
    # 獲取每種食材的使用詳情
    ingredients_with_details = []
    for ing in top_ingredients:
        menu_items = MenuItem.objects.filter(ingredients__ingredient=ing, is_available=True)
        restaurants = Restaurant.objects.filter(menu_items__in=menu_items).distinct()
        
        # 計算包含此食材的菜單平均營養值
        avg_nutrition = menu_items.aggregate(
            avg_calories=Avg('nutrition__calories'),
            avg_protein=Avg('nutrition__protein'),
            avg_carbs=Avg('nutrition__carbs'),
            avg_fat=Avg('nutrition__fat')
        )
        
        ingredients_with_details.append({
            'ingredient': ing,
            'menu_items': menu_items[:6],
            'menu_item_count': menu_items.count(),
            'restaurant_count': restaurants.count(),
            'avg_nutrition': avg_nutrition
        })
    
    # 食材分類統計
    ingredient_categories = {
        'vegetables': Ingredient.objects.filter(
            name__in=['番茄', '洋蔥', '高麗菜', '紅蘿蔔', '青椒', '菠菜', '生菜']
        ).annotate(usage_count=Count('menu_items')).order_by('-usage_count'),
        'proteins': Ingredient.objects.filter(
            name__in=['雞肉', '豬肉', '牛肉', '魚肉', '蛋', '豆腐', '蝦']
        ).annotate(usage_count=Count('menu_items')).order_by('-usage_count'),
        'grains': Ingredient.objects.filter(
            name__in=['米飯', '麵條', '麵包', '玉米', '燕麥', '藜麥']
        ).annotate(usage_count=Count('menu_items')).order_by('-usage_count'),
        'dairy': Ingredient.objects.filter(
            name__in=['牛奶', '起司', '奶油', '優格', '鮮奶油']
        ).annotate(usage_count=Count('menu_items')).order_by('-usage_count')
    }
    
    # 營養密度高的食材
    nutritious_ingredients = [
        {
            'name': '菠菜',
            'benefits': '富含鐵質、維生素K、葉酸',
            'calories_per_100g': 23,
            'protein_per_100g': 2.9,
            'health_benefits': '改善貧血、強化骨骼、促進心血管健康'
        },
        {
            'name': '鮭魚',
            'benefits': '富含Omega-3脂肪酸、優質蛋白質',
            'calories_per_100g': 208,
            'protein_per_100g': 25.4,
            'health_benefits': '降低心臟病風險、改善腦部功能、抗發炎'
        },
        {
            'name': '藜麥',
            'benefits': '完整蛋白質、高纖維、無麩質',
            'calories_per_100g': 368,
            'protein_per_100g': 14.1,
            'health_benefits': '穩定血糖、促進消化、提供持久能量'
        },
        {
            'name': '酪梨',
            'benefits': '健康脂肪、維生素E、鉀',
            'calories_per_100g': 160,
            'protein_per_100g': 2.0,
            'health_benefits': '降低膽固醇、保護心臟、促進營養吸收'
        }
    ]
    
    # 食材使用趨勢
    ingredient_trends = {
        'rising': ['藜麥', '酪梨', '羽衣甘藍', '奇亞籽', '椰子油'],
        'stable': ['雞肉', '米飯', '番茄', '洋蔥', '蛋'],
        'declining': ['豬油', '白糖', '精製麵粉', '人工添加劑']
    }
    
    return render(request, 'food_analysis/ingredient_analysis.html', {
        'ingredients_with_details': ingredients_with_details,
        'ingredient_categories': ingredient_categories,
        'nutritious_ingredients': nutritious_ingredients,
        'ingredient_trends': ingredient_trends,
    })

def ai_nutrition_advisor(request):
    """智能營養顧問，使用AI回答飲食和營養相關問題，並產生營養圖表"""
    question = request.GET.get('question', '')
    response = None
    recommendations = []
    analysis_result = None
    chart_data = None

    if question:
        # 呼叫 AI 分析（複用 analyze_food）
        analysis_result = analyze_food(question)
        response = analysis_result.get('nutritional_value', '')
        # 準備圖表數據
        chart_data = {
            'nutrition_pie': {
                'labels': ['蛋白質', '碳水化合物', '脂肪'],
                'data': [
                    analysis_result.get('protein', 0),
                    analysis_result.get('carbs', 0),
                    analysis_result.get('fat', 0)
                ]
            },
            'nutrition_bar': {
                'labels': ['熱量', '蛋白質', '碳水化合物', '脂肪'],
                'data': [
                    analysis_result.get('calories', 0),
                    analysis_result.get('protein', 0),
                    analysis_result.get('carbs', 0),
                    analysis_result.get('fat', 0)
                ]
            },
            'radar': {
                'labels': ['蛋白質', '碳水化合物', '脂肪', '纖維', '糖分', '鈉'],
                'data': [
                    analysis_result.get('protein', 0),
                    analysis_result.get('carbs', 0),
                    analysis_result.get('fat', 0),
                    analysis_result.get('fiber', 0),
                    analysis_result.get('sugar', 0),
                    analysis_result.get('sodium', 0)
                ]
            }
        }
        # 保留原本的推薦菜單邏輯
        recommendations = recommend_menu_items(question)

    return render(request, 'food_analysis/ai_advisor.html', {
        'question': question,
        'response': response,
        'analysis_result': analysis_result,
        'chart_data': chart_data,
        'recommendations': recommendations,
    })

def generate_ai_response(question):
    """模擬AI回答生成（實際應用中應該調用AI API）"""
    # 關鍵詞匹配的簡單示例
    responses = {
        '減肥': '減肥的關鍵是營造熱量赤字，每天攝入的熱量少於消耗的熱量。建議增加蛋白質攝入，減少精製碳水和添加糖，多吃蔬菜水果，並保持適當的運動量。',
        '蛋白質': '蛋白質是身體的重要建構元素，成人每天建議攝入體重每公斤1.2-2.0克的蛋白質。優質蛋白質來源包括瘦肉、魚類、雞蛋、豆類、堅果和乳製品。',
        '素食': '素食飲食需要特別注意蛋白質、鐵、鋅、鈣、維生素B12和omega-3脂肪酸的攝取。建議多樣化食物選擇，包括豆類、全穀物、堅果種子、豆腐等。',
        '糖尿病': '糖尿病患者應控制碳水化合物攝入，選擇低GI食物，增加纖維攝入，減少添加糖和精製碳水，保持規律進餐時間，控制份量。',
        '高血壓': '高血壓患者建議遵循DASH飲食法，減少鈉攝入，增加鉀、鎂、鈣的攝入，多吃蔬果，減少加工食品，限制酒精攝入。',
    }
    
    # 簡單的關鍵詞匹配
    for keyword, answer in responses.items():
        if keyword in question:
            return answer
    
    # 預設回答
    return '我是您的智能營養顧問，可以回答有關飲食、營養和健康的問題。您可以詢問特定食物的營養價值、減肥建議、各種飲食方式的優缺點等問題。'

def recommend_menu_items(question):
    """根據問題推薦菜單項目（實際應用中應該基於語義分析）"""
    # 嘗試從資料庫中尋找相關菜單項
    menu_items = MenuItem.objects.filter(is_available=True)
    
    # 如果沒有足夠的項目，返回空列表
    if menu_items.count() < 3:
        return []
    
    # 隨機選擇3個項目作為推薦（實際應用中應該基於語義相關性）
    # 在實際應用中，這裡可以使用更複雜的算法來篩選最相關的項目
    sample_size = min(3, menu_items.count())
    recommended_items = random.sample(list(menu_items), sample_size)
    
    return recommended_items

def ai_food_analysis(request):
    """AI食物分析功能，分析用戶輸入的食物並提供詳細的營養分析"""
    if request.method == 'POST':
        form = FoodAnalysisForm(request.POST)
        if form.is_valid():
            food_description = form.cleaned_data['food_description']
            
            # 分析結果
            analysis_result = analyze_food(food_description)
            
            # 準備圖表數據
            chart_data = {
                'nutrition_bar': {
                    'labels': ['熱量', '蛋白質', '碳水化合物', '總脂肪', '飽和脂肪', '反式脂肪', '糖', '鈉'],
                    'data': [
                        analysis_result.get('calories', 0),
                        analysis_result.get('protein', 0),
                        analysis_result.get('carbs', 0),
                        analysis_result.get('fat', 0),
                        analysis_result.get('saturated_fat', 0),
                        analysis_result.get('trans_fat', 0),
                        analysis_result.get('sugar', 0),
                        analysis_result.get('sodium', 0)
                    ]
                },
                'radar': {
                    'labels': ['蛋白質', '碳水化合物', '脂肪', '纖維', '糖分', '鈉'],
                    'data': [
                        analysis_result.get('protein', 0),
                        analysis_result.get('carbs', 0),
                        analysis_result.get('fat', 0),
                        analysis_result.get('fiber', 0),
                        analysis_result.get('sugar', 0),
                        analysis_result.get('sodium', 0)
                    ]
                }
            }
            
            return render(request, 'food_analysis/ai_food_analysis.html', {
                'form': form,
                'food_description': food_description,
                'analysis_result': analysis_result,
                'chart_data': chart_data
            })
        else:
            return render(request, 'food_analysis/ai_food_analysis.html', {
                'form': form,
            })
    else:
        form = FoodAnalysisForm()
    return render(request, 'food_analysis/ai_food_analysis.html', {
        'form': form,
    })

def analyze_food(food_description):
    """使用 Together AI 分析食物描述並返回詳細的營養分析結果"""
    try:
        # 強化 prompt，要求 AI 回傳所有欄位內容，並參考台灣常見食物營養資料庫
        prompt = f"""
請分析以下食物的營養成分：{food_description}

請只回傳純JSON格式，不要包含任何註解或額外文字：
{{
    "calories": 數值,
    "protein": 數值,
    "carbs": 數值,
    "fat": 數值,
    "saturated_fat": 數值,
    "trans_fat": 數值,
    "fiber": 數值,
    "sugar": 數值,
    "sodium": 數值,
    "nutritional_value": "營養價值分析文字",
    "health_impact": "健康影響分析文字",
    "improvement_suggestions": ["建議1", "建議2", "建議3"]
}}"""

        # 調用 Together AI API
        print(f"正在使用 Together AI API 進行分析，模型：mistralai/Mixtral-8x7B-Instruct-v0.1")
        response = together.Complete.create(
            prompt=prompt,
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            max_tokens=1000,
            temperature=0.7,
            top_p=0.9,
            top_k=50,
            repetition_penalty=1.1,
            stop=['</s>', 'Human:', 'Assistant:']
        )
        print(f"Together AI API 回應：{response}")

        # 解析回應
        try:
            # 新的回應格式處理
            response_text = response['choices'][0]['text']
            print("Together AI 回傳內容：", response_text)
            
            # 清理回應文本，移除可能的前綴和後綴
            response_text = response_text.strip()
            
            # 尋找JSON開始和結束位置
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end <= json_start:
                raise ValueError("無法在回應中找到有效的 JSON")
            
            json_str = response_text[json_start:json_end]
            
            # 清理JSON字符串中的註解
            json_str = re.sub(r'//.*?\n', '\n', json_str)  # 移除單行註解
            json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)  # 移除多行註解
            
            # 嘗試解析JSON
            analysis_result = json.loads(json_str)
            
            # 檢查所有欄位，若缺少則補預設值
            default_result = {
                'calories': 0,
                'protein': 0,
                'carbs': 0,
                'fat': 0,
                'saturated_fat': 0,
                'trans_fat': 0,
                'fiber': 0,
                'sugar': 0,
                'sodium': 0,
                'nutritional_value': '無法取得營養價值分析',
                'health_impact': '無法取得健康影響分析',
                'improvement_suggestions': ['請提供更詳細的食物描述', '建議諮詢專業營養師', '注意均衡飲食']
            }
            for key in default_result:
                if key not in analysis_result or not analysis_result[key]:
                    analysis_result[key] = default_result[key]
            return analysis_result
        except (json.JSONDecodeError, KeyError, IndexError, ValueError) as e:
            print(f"解析 Together AI 回應時出錯: {str(e)}")
            # 將 AI 回傳的原始內容也傳給前端
            return {
                'calories': 0,
                'protein': 0,
                'carbs': 0,
                'fat': 0,
                'saturated_fat': 0,
                'trans_fat': 0,
                'fiber': 0,
                'sugar': 0,
                'sodium': 0,
                'nutritional_value': '系統暫時無法分析，請稍後再試。',
                'health_impact': '系統暫時無法評估，請稍後再試。',
                'improvement_suggestions': [
                    '請提供更詳細的食物描述',
                    '建議諮詢專業營養師',
                    '注意均衡飲食'
                ],
                'ai_raw_response': response_text if 'response_text' in locals() else str(e)
            }
    except Exception as e:
        print(f"Together AI API 調用出錯: {str(e)}")
        return {
            'calories': 0,
            'protein': 0,
            'carbs': 0,
            'fat': 0,
            'saturated_fat': 0,
            'trans_fat': 0,
            'fiber': 0,
            'sugar': 0,
            'sodium': 0,
            'nutritional_value': '系統暫時無法分析，請稍後再試。',
            'health_impact': '系統暫時無法評估，請稍後再試。',
            'improvement_suggestions': [
                '請稍後再試',
                '如果問題持續，請聯繫管理員',
                '您可以先查看其他食物的分析'
            ],
            'ai_raw_response': str(e)
        }

@login_required
def personal_food_diary(request):
    """個人飲食日記 - 記錄和查看個人飲食"""
    if request.method == 'POST':
        form = PersonalFoodRecordForm(request.POST)
        if form.is_valid():
            food_record = form.save(commit=False)
            food_record.user = request.user
            
            # 使用 AI 分析食物
            analysis_result = analyze_food(food_record.food_description)
            
            # 保存 AI 分析結果
            food_record.calories = analysis_result.get('calories', 0)
            food_record.protein = analysis_result.get('protein', 0)
            food_record.carbs = analysis_result.get('carbs', 0)
            food_record.fat = analysis_result.get('fat', 0)
            food_record.fiber = analysis_result.get('fiber', 0)
            food_record.sugar = analysis_result.get('sugar', 0)
            food_record.sodium = analysis_result.get('sodium', 0)
            food_record.nutritional_analysis = analysis_result.get('nutritional_value', '')
            food_record.health_impact = analysis_result.get('health_impact', '')
            food_record.improvement_suggestions = analysis_result.get('improvement_suggestions', [])
            
            food_record.save()
            
            # 更新當日營養總結
            update_daily_nutrition_summary(request.user, food_record.date_consumed)
            
            messages.success(request, f'成功記錄您的{food_record.get_meal_type_display()}！AI 已完成營養分析。')
            return redirect('personal_food_diary')
    else:
        form = PersonalFoodRecordForm()
    
    # 獲取用戶最近的飲食記錄
    recent_records = PersonalFoodRecord.objects.filter(user=request.user)[:10]
    
    # 獲取今日營養總結
    today = timezone.now().date()
    today_summary, created = PersonalNutritionSummary.objects.get_or_create(
        user=request.user,
        date=today,
        defaults={
            'total_calories': 0,
            'total_protein': 0,
            'total_carbs': 0,
            'total_fat': 0,
            'total_fiber': 0,
            'total_sugar': 0,
            'total_sodium': 0,
            'meal_count': 0
        }
    )
    
    # 獲取最近7天的營養趨勢
    week_summaries = PersonalNutritionSummary.objects.filter(
        user=request.user,
        date__gte=today - timedelta(days=6)
    ).order_by('date')
    
    return render(request, 'food_analysis/personal_diary.html', {
        'form': form,
        'recent_records': recent_records,
        'today_summary': today_summary,
        'week_summaries': week_summaries,
    })

def update_daily_nutrition_summary(user, date):
    """更新用戶當日營養總結"""
    daily_records = PersonalFoodRecord.objects.filter(
        user=user,
        date_consumed=date
    )
    
    # 計算當日總營養
    totals = daily_records.aggregate(
        total_calories=Sum('calories'),
        total_protein=Sum('protein'),
        total_carbs=Sum('carbs'),
        total_fat=Sum('fat'),
        total_fiber=Sum('fiber'),
        total_sugar=Sum('sugar'),
        total_sodium=Sum('sodium'),
        meal_count=Count('id')
    )
    
    # 更新或創建營養總結
    summary, created = PersonalNutritionSummary.objects.update_or_create(
        user=user,
        date=date,
        defaults={
            'total_calories': totals['total_calories'] or 0,
            'total_protein': totals['total_protein'] or 0,
            'total_carbs': totals['total_carbs'] or 0,
            'total_fat': totals['total_fat'] or 0,
            'total_fiber': totals['total_fiber'] or 0,
            'total_sugar': totals['total_sugar'] or 0,
            'total_sodium': totals['total_sodium'] or 0,
            'meal_count': totals['meal_count'] or 0
        }
    )

@login_required
def personal_nutrition_dashboard(request):
    """個人營養儀表板 - 基於用戶的飲食記錄"""
    user = request.user
    today = timezone.now().date()
    
    # 獲取今日營養總結
    today_summary = PersonalNutritionSummary.objects.filter(
        user=user, date=today
    ).first()
    
    # 獲取最近7天的營養數據
    week_summaries = PersonalNutritionSummary.objects.filter(
        user=user,
        date__gte=today - timedelta(days=6)
    ).order_by('date')
    
    # 獲取最近的飲食記錄
    recent_records = PersonalFoodRecord.objects.filter(user=user)[:5]
    
    # 計算平均營養攝入
    avg_nutrition = PersonalNutritionSummary.objects.filter(
        user=user,
        date__gte=today - timedelta(days=30)
    ).aggregate(
        avg_calories=Avg('total_calories'),
        avg_protein=Avg('total_protein'),
        avg_carbs=Avg('total_carbs'),
        avg_fat=Avg('total_fat')
    )
    
    # 每日營養建議值
    daily_recommendations = {
        'calories': 2000,
        'protein': 50,
        'carbs': 300,
        'fat': 65,
        'fiber': 25,
        'sugar': 50,
        'sodium': 2300
    }
    
    # 計算達成率
    achievement_rates = {}
    if today_summary:
        achievement_rates = {
            'calories': min((today_summary.total_calories / daily_recommendations['calories']) * 100, 100),
            'protein': min((today_summary.total_protein / daily_recommendations['protein']) * 100, 100),
            'carbs': min((today_summary.total_carbs / daily_recommendations['carbs']) * 100, 100),
            'fat': min((today_summary.total_fat / daily_recommendations['fat']) * 100, 100),
        }
    
    return render(request, 'food_analysis/personal_dashboard.html', {
        'today_summary': today_summary,
        'week_summaries': week_summaries,
        'recent_records': recent_records,
        'avg_nutrition': avg_nutrition,
        'daily_recommendations': daily_recommendations,
        'achievement_rates': achievement_rates,
    })

def ai_nutrition_consultant(request):
    """全新的AI營養顧問 - 專業營養師互動式諮詢"""
    conversation_history = request.session.get('nutrition_conversation', [])
    
    # 處理AJAX請求
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
            
            # 處理清除對話
            if data.get('action') == 'clear_chat':
                request.session['nutrition_conversation'] = []
                return JsonResponse({'success': True})
            
            user_question = data.get('question', '').strip()
            
            if user_question:
                # 將用戶問題添加到對話歷史
                conversation_history.append({
                    'role': 'user',
                    'content': user_question,
                    'timestamp': timezone.now().isoformat()
                })
                
                # 生成AI回應
                ai_response = get_nutrition_consultant_response(user_question, conversation_history)
                
                # 將AI回應添加到對話歷史
                conversation_history.append({
                    'role': 'assistant',
                    'content': ai_response,
                    'timestamp': timezone.now().isoformat()
                })
                
                # 保存對話歷史到session（限制最近20條對話）
                request.session['nutrition_conversation'] = conversation_history[-20:]
                
                return JsonResponse({
                    'success': True,
                    'response': ai_response
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': '請輸入您的問題'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'發生錯誤：{str(e)}'
            })
    
    # GET請求：顯示頁面
    return render(request, 'food_analysis/ai_nutrition_consultant.html', {
        'conversation_history': conversation_history
    })

def get_nutrition_consultant_response(question, conversation_history):
    """獲取AI營養顧問的專業回應"""
    try:
        # 檢查API密鑰
        api_key = settings.TOGETHER_API_KEY
        if not api_key:
            return "API設定錯誤，請聯繫管理員。"
        
        # 清理輸入
        clean_question = str(question).strip()[:100]  # 限制為100字符
        if not clean_question:
            return "請輸入您的問題。"
        
        # 使用穩定的Llama模型和最簡單的請求格式
        request_data = {
            "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
            "messages": [
                {"role": "user", "content": f"作為營養師，請用繁體中文簡潔回答：{clean_question}"}
            ],
            "max_tokens": 200,
            "temperature": 0.5
        }
        
        # 調用Together AI API
        response = requests.post(
            "https://api.together.xyz/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=request_data,
            timeout=25
        )
        
        # 處理回應
        if response.status_code == 200:
            try:
                data = response.json()
                if 'choices' in data and data['choices']:
                    content = data['choices'][0]['message']['content']
                    return content.strip()[:500] if content else "AI營養師暫時無法回應。"
                return "AI營養師回應格式異常。"
            except (json.JSONDecodeError, KeyError, IndexError):
                return "回應解析失敗。"
        else:
            # 簡化錯誤處理
            return f"服務暫時不可用（錯誤{response.status_code}），請稍後再試。"
            
    except requests.exceptions.Timeout:
        return "請求超時，請稍後再試。"
    except requests.exceptions.ConnectionError:
        return "網路連接問題，請檢查網路。"
    except Exception as e:
        return f"系統錯誤：{str(e)[:50]}"

@login_required
def delete_food_record(request, record_id):
    """刪除飲食記錄"""
    record = get_object_or_404(PersonalFoodRecord, id=record_id, user=request.user)
    record_date = record.date_consumed
    if hasattr(record_date, 'date'):
        record_date = record_date.date()
    record.delete()
    
    # 更新該日期的營養總結
    update_daily_nutrition_summary(request.user, record_date)
    
    messages.success(request, '飲食記錄已成功刪除')
    return redirect('personal_food_diary')
