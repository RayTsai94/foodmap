from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Avg, Sum, Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from restaurants.models import MenuItem, Restaurant
from .models import NutritionInfo, Ingredient, FoodPreference, UserFoodRecord, UserFoodIngredient
from .forms import UserFoodRecordForm, UserFoodIngredientFormSet, FoodAnalysisForm, SaveAnalysisToRecordForm
import random
import json
import requests
import re

def nutrition_dashboard(request):
    """營養分析儀表板，提供整體食品營養概覽"""
    # 獲取所有有營養信息的菜單項
    menu_items_with_nutrition = MenuItem.objects.filter(nutrition__isnull=False)
    
    # 計算平均營養值
    avg_nutrition = NutritionInfo.objects.aggregate(
        avg_calories=Avg('calories'),
        avg_protein=Avg('protein'),
        avg_carbs=Avg('carbs'),
        avg_fat=Avg('fat')
    )
    
    # 獲取低熱量（健康）選擇
    healthy_choices = MenuItem.objects.filter(
        nutrition__calories__lt=500,
        is_available=True
    ).order_by('nutrition__calories')[:5]
    
    # 按餐廳分組的營養信息
    restaurant_nutrition = Restaurant.objects.filter(
        menu_items__nutrition__isnull=False
    ).distinct().annotate(
        avg_calories=Avg('menu_items__nutrition__calories')
    ).order_by('avg_calories')
    
    return render(request, 'food_analysis/dashboard.html', {
        'avg_nutrition': avg_nutrition,
        'healthy_choices': healthy_choices,
        'restaurant_nutrition': restaurant_nutrition,
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
            preferences_with_items.append({
                'preference': pref,
                'items': compatible_items[:5],  # 僅顯示前5項
                'total_count': compatible_items.count()
            })
    
    return render(request, 'food_analysis/dietary_preferences.html', {
        'preferences_with_items': preferences_with_items,
    })

def allergen_info(request):
    """過敏原信息頁面，顯示常見過敏原和不含這些過敏原的菜單項"""
    # 獲取所有過敏原偏好
    allergens = FoodPreference.objects.filter(type='ALLERGY')
    
    # 為每個過敏原獲取不兼容的菜單項
    allergen_free_items = []
    for allergen in allergens:
        free_items = MenuItem.objects.filter(
            preferences__preference=allergen,
            preferences__is_compatible=False,
            is_available=True
        )
        
        if free_items.exists():
            allergen_free_items.append({
                'allergen': allergen,
                'items': free_items[:5],
                'total_count': free_items.count()
            })
    
    return render(request, 'food_analysis/allergen_info.html', {
        'allergen_free_items': allergen_free_items,
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
        menu_items = MenuItem.objects.filter(ingredients__ingredient=ing)
        restaurants = Restaurant.objects.filter(menu_items__in=menu_items).distinct()
        
        ingredients_with_details.append({
            'ingredient': ing,
            'menu_items': menu_items[:5],
            'menu_item_count': menu_items.count(),
            'restaurant_count': restaurants.count()
        })
    
    return render(request, 'food_analysis/ingredient_analysis.html', {
        'ingredients_with_details': ingredients_with_details,
    })

def ai_nutrition_advisor(request):
    """智能營養顧問，使用AI回答飲食和營養相關問題"""
    question = request.GET.get('question', '')
    response = None
    recommendations = []
    
    if question:
        # 在這裡我們模擬AI回答，實際應用中可以接入OpenAI或Together.ai等API
        response = generate_ai_response(question)
        
        # 根據問題推薦菜單項目
        recommendations = recommend_menu_items(question)
    
    return render(request, 'food_analysis/ai_advisor.html', {
        'question': question,
        'response': response,
        'recommendations': recommendations,
    })

def generate_ai_response(question):
    """使用Together.ai API生成AI回答"""
    # 檢查是否配置了API密鑰
    api_key = settings.TOGETHER_API_KEY
    if not api_key:
        return "AI服務暫時不可用，請稍後再試。"
    
    try:
        # 準備API請求
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # 構建提示
        prompt = f"""你是一位專業的營養師和飲食顧問。請用中文回答以下關於飲食和營養的問題，並盡可能提供科學依據和具體建議：
        
        問題：{question}
        
        請提供準確、實用且詳細的回答，但不要太長。"""
        
        # API請求數據
        data = {
            "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "prompt": prompt,
            "max_tokens": 800,
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        # 發送請求
        response = requests.post(
            "https://api.together.xyz/v1/completions",
            headers=headers,
            json=data
        )
        
        # 檢查響應
        if response.status_code == 200:
            result = response.json()
            answer = result.get("choices", [{}])[0].get("text", "").strip()
            return answer if answer else "抱歉，無法生成回答。請重新提問或稍後再試。"
        else:
            return f"AI服務暫時不可用 (錯誤碼: {response.status_code})，請稍後再試。"
            
    except Exception as e:
        return f"處理您的請求時發生錯誤: {str(e)}。請稍後再試。"

def recommend_menu_items(question):
    """根據問題推薦菜單項目（基於關鍵詞匹配）"""
    # 獲取所有可用的菜單項
    menu_items = MenuItem.objects.filter(is_available=True)
    
    # 如果沒有足夠的項目，返回空列表
    if menu_items.count() < 3:
        return []
    
    # 關鍵詞字典
    keywords = {
        '減肥': ['低卡', '低熱量', '健康', '蔬菜', '輕食'],
        '蛋白質': ['肉', '雞胸', '牛肉', '魚', '蛋', '豆腐', '奶製品'],
        '素食': ['素', '蔬菜', '豆腐', '沙拉'],
        '糖尿病': ['低糖', '低碳水', '全穀物'],
        '高血壓': ['低鈉', '低鹽', '地中海'],
    }
    
    matching_items = []
    
    # 檢查問題中是否包含關鍵詞
    for key, word_list in keywords.items():
        if key in question:
            # 為每個關鍵詞檢查菜單項目名稱和描述
            for item in menu_items:
                if any(word in item.name.lower() or 
                      (item.description and word in item.description.lower()) 
                      for word in word_list):
                    matching_items.append(item)
    
    # 去重
    matching_items = list(set(matching_items))
    
    # 如果沒有匹配項目，返回隨機推薦
    if not matching_items:
        sample_size = min(3, menu_items.count())
        return random.sample(list(menu_items), sample_size)
    
    # 如果匹配項目超過3個，只返回3個
    if len(matching_items) > 3:
        return random.sample(matching_items, 3)
    
    return matching_items

@login_required
def user_food_record(request):
    """用戶食物記錄管理"""
    # 獲取用戶的所有食物記錄
    user_records = UserFoodRecord.objects.filter(user=request.user).order_by('-date_consumed')
    
    # 處理新記錄提交
    if request.method == 'POST':
        form = UserFoodRecordForm(request.POST, request.FILES)
        if form.is_valid():
            # 創建但不保存記錄
            record = form.save(commit=False)
            record.user = request.user
            record.save()
            
            # 保存配料
            formset = UserFoodIngredientFormSet(request.POST, instance=record)
            if formset.is_valid():
                formset.save()
                messages.success(request, '成功添加食物記錄！')
                return redirect('user_food_record')
    else:
        form = UserFoodRecordForm()
        formset = UserFoodIngredientFormSet()
    
    return render(request, 'food_analysis/user_food_record.html', {
        'form': form,
        'formset': formset,
        'user_records': user_records,
    })

def ai_food_analysis(request):
    """AI食物分析功能"""
    form = FoodAnalysisForm()
    save_form = SaveAnalysisToRecordForm()
    analysis_result = None
    food_description = ""
    
    if request.method == 'POST':
        # 檢查是否是保存分析結果的提交
        if 'save_to_record' in request.POST:
            save_form = SaveAnalysisToRecordForm(request.POST, request.FILES)
            if save_form.is_valid() and request.user.is_authenticated:
                # 創建食物記錄
                record = save_form.save(commit=False)
                record.user = request.user
                record.description = request.POST.get('food_description', '')
                
                # 保存營養數據
                record.calories = request.POST.get('calories', None)
                record.protein = request.POST.get('protein', None)
                record.carbs = request.POST.get('carbs', None)
                record.fat = request.POST.get('fat', None)
                
                record.save()
                messages.success(request, '成功保存食物分析結果到您的記錄！')
                return redirect('user_food_record')
            elif not request.user.is_authenticated:
                messages.error(request, '您需要登入才能保存食物記錄。')
        else:
            # 正常的分析請求
            form = FoodAnalysisForm(request.POST)
            if form.is_valid():
                food_description = form.cleaned_data['food_description']
                
                # 使用Together.ai API進行分析
                api_key = settings.TOGETHER_API_KEY
                if not api_key:
                    messages.error(request, "AI服務暫時不可用，請稍後再試。")
                else:
                    try:
                        # 準備API請求
                        headers = {
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json"
                        }
                        
                        # 構建提示，更強調結構化回應
                        prompt = f"""你是一位專業的營養師和飲食顧問。請分析以下食物的營養成分和健康影響：
                        
                        食物：{food_description}
                        
                        請提供以下資訊：
                        1. 大致的熱量、蛋白質、碳水化合物和脂肪含量的估計值
                        2. 這些食物的營養價值評價
                        3. 對健康的可能影響
                        4. 如何使這頓飯更健康的建議
                        
                        請務必使用下面的JSON格式回答，確保它是有效的JSON格式：
                        {{
                            "calories": 數字,
                            "protein": 數字,
                            "carbs": 數字,
                            "fat": 數字,
                            "nutritional_value": "營養價值評價文字",
                            "health_impact": "健康影響分析文字",
                            "improvement_suggestions": ["建議1", "建議2", "建議3", "建議4"]
                        }}
                        """
                        
                        # API請求數據
                        data = {
                            "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
                            "prompt": prompt,
                            "max_tokens": 1000,
                            "temperature": 0.7,
                            "top_p": 0.9
                        }
                        
                        # 發送請求
                        response = requests.post(
                            "https://api.together.xyz/v1/completions",
                            headers=headers,
                            json=data
                        )
                        
                        # 檢查響應
                        if response.status_code == 200:
                            result = response.json()
                            answer_text = result.get("choices", [{}])[0].get("text", "").strip()
                            
                            # 嘗試解析JSON，改進的解析邏輯
                            try:
                                # 使用正則表達式找到JSON部分
                                import re
                                
                                # 嘗試找到JSON對象
                                json_match = re.search(r'\{[\s\S]*?\}', answer_text)
                                if json_match:
                                    json_str = json_match.group(0)
                                    
                                    # 嘗試清理JSON字符串中的問題
                                    # 處理可能的trailing commas
                                    json_str = re.sub(r',\s*}', '}', json_str)
                                    json_str = re.sub(r',\s*]', ']', json_str)
                                    
                                    # 嘗試解析
                                    try:
                                        analysis_result = json.loads(json_str)
                                    except json.JSONDecodeError as e:
                                        # 如果仍然失敗，使用更寬鬆的解析方法
                                        import ast
                                        try:
                                            # 使用ast.literal_eval來解析字典
                                            cleaned_str = json_str.replace('null', 'None')
                                            parsed_dict = ast.literal_eval(cleaned_str)
                                            analysis_result = {k: (v if v != None else '') for k, v in parsed_dict.items()}
                                        except (SyntaxError, ValueError):
                                            # 最後的嘗試：提取個別欄位
                                            analysis_result = extract_fields_from_text(answer_text)
                                else:
                                    # 如果找不到JSON，嘗試提取欄位
                                    analysis_result = extract_fields_from_text(answer_text)
                                    
                                # 確保improvement_suggestions是列表
                                if 'improvement_suggestions' in analysis_result and not isinstance(analysis_result['improvement_suggestions'], list):
                                    try:
                                        # 嘗試轉換字符串到列表
                                        if isinstance(analysis_result['improvement_suggestions'], str):
                                            suggestions = analysis_result['improvement_suggestions']
                                            # 按行分割或按逗號分割
                                            if '\n' in suggestions:
                                                suggestions_list = [s.strip() for s in suggestions.split('\n') if s.strip()]
                                            else:
                                                suggestions_list = [s.strip() for s in suggestions.split(',') if s.strip()]
                                            analysis_result['improvement_suggestions'] = suggestions_list
                                    except:
                                        # 如果轉換失敗，保持原樣
                                        pass
                                    
                            except Exception as e:
                                analysis_result = {
                                    "text_response": answer_text,
                                    "error": f"解析JSON時發生錯誤: {str(e)}"
                                }
                        else:
                            messages.error(request, f"AI服務暫時不可用 (錯誤碼: {response.status_code})，請稍後再試。")
                            
                        # 如果分析成功，預先填充保存記錄表單
                        if analysis_result and not analysis_result.get('error'):
                            # 從食物描述中提取可能的食物名稱
                            food_name = food_description.split('、')[0] if '、' in food_description else food_description
                            if len(food_name) > 50:  # 名稱太長，截斷
                                food_name = food_name[:47] + '...'
                            save_form = SaveAnalysisToRecordForm(initial={'name': food_name})
                    
                    except Exception as e:
                        messages.error(request, f"處理您的請求時發生錯誤: {str(e)}。請稍後再試。")
    
    return render(request, 'food_analysis/ai_food_analysis.html', {
        'form': form,
        'save_form': save_form,
        'analysis_result': analysis_result,
        'food_description': food_description,
    })

def extract_fields_from_text(text):
    """從文本中提取營養分析字段"""
    result = {}
    
    # 提取數字字段
    calorie_match = re.search(r'熱量.*?(\d+)', text) or re.search(r'卡路里.*?(\d+)', text) or re.search(r'calories.*?(\d+)', text)
    if calorie_match:
        result['calories'] = int(calorie_match.group(1))
        
    protein_match = re.search(r'蛋白質.*?(\d+)', text) or re.search(r'protein.*?(\d+)', text)
    if protein_match:
        result['protein'] = int(protein_match.group(1))
        
    carbs_match = re.search(r'碳水化合物.*?(\d+)', text) or re.search(r'carbs.*?(\d+)', text)
    if carbs_match:
        result['carbs'] = int(carbs_match.group(1))
        
    fat_match = re.search(r'脂肪.*?(\d+)', text) or re.search(r'fat.*?(\d+)', text)
    if fat_match:
        result['fat'] = int(fat_match.group(1))
    
    # 提取文本字段
    # 用于分段的常见标题
    sections = [
        ('營養價值', 'nutritional_value'),
        ('健康影響', 'health_impact'),
        ('改善建議', 'improvement_suggestions')
    ]
    
    lines = text.split('\n')
    current_section = None
    section_content = []
    
    for line in lines:
        matched = False
        for title, key in sections:
            if re.search(f'{title}', line, re.IGNORECASE):
                # 保存先前的部分
                if current_section:
                    result[current_section] = '\n'.join(section_content).strip()
                # 開始新部分
                current_section = key
                section_content = []
                matched = True
                break
        
        if not matched and current_section and line.strip():
            section_content.append(line.strip())
    
    # 保存最後一個部分
    if current_section and section_content:
        if current_section == 'improvement_suggestions':
            result[current_section] = [item for item in section_content if item]
        else:
            result[current_section] = '\n'.join(section_content).strip()
            
    # 如果仍然沒有解析出字段，保存整個文本
    if not result:
        result['text_response'] = text
        result['error'] = "無法解析結構化數據"
        
    return result

@login_required
def save_analysis_to_record(request):
    """直接儲存分析結果到食物記錄（AJAX呼叫）"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            food_name = data.get('food_name', '未命名食物')
            food_description = data.get('food_description', '')
            
            # 創建食物記錄
            record = UserFoodRecord(
                user=request.user,
                name=food_name,
                description=food_description,
                calories=data.get('calories'),
                protein=data.get('protein'),
                carbs=data.get('carbs'),
                fat=data.get('fat')
            )
            record.save()
            
            return JsonResponse({'success': True, 'message': '成功儲存食物記錄！'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'儲存失敗: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': '請求方式不正確'})

@login_required
def delete_food_record(request, record_id):
    """刪除用戶的食物記錄"""
    record = get_object_or_404(UserFoodRecord, id=record_id, user=request.user)
    record.delete()
    messages.success(request, '成功刪除食物記錄！')
    return redirect('user_food_record')

def ai_restaurant_matcher(request):
    """使用Together AI分析用戶關鍵詞並匹配Google Maps上的餐廳"""
    search_form = FoodAnalysisForm()  # 重用現有表單，或創建新表單
    search_results = []
    search_query = ""
    ai_analysis = None
    
    if request.method == 'POST':
        search_form = FoodAnalysisForm(request.POST)
        if search_form.is_valid():
            search_query = search_form.cleaned_data['food_description']
            
            # 使用Together AI分析用戶關鍵詞
            ai_analysis = analyze_food_keywords(search_query)
            
            if ai_analysis:
                # 基於AI分析結果搜索餐廳
                search_results = search_restaurants_by_keywords(ai_analysis)
    
    return render(request, 'food_analysis/ai_restaurant_matcher.html', {
        'form': search_form,
        'search_results': search_results,
        'search_query': search_query,
        'ai_analysis': ai_analysis,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
    })

def analyze_food_keywords(query):
    """使用Together AI分析用戶的餐廳搜索關鍵詞"""
    api_key = settings.TOGETHER_API_KEY
    if not api_key:
        return None
    
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # 構建提示
        prompt = f"""你是一位專業的餐飲分析師。請分析以下用戶搜索關鍵詞，並提取與餐廳和食物相關的關鍵信息：
        
        用戶搜索：{query}
        
        請提取以下信息：
        1. 菜系或食物類型（例如：中式、日式、快餐、素食等）
        2. 特定食物名稱或菜品（例如：牛排、壽司、漢堡等）
        3. 價格範圍或預算考量（例如：平價、高檔等）
        4. 特殊飲食需求（例如：素食、無麩質、低卡路里等）
        5. 用戶可能想要的用餐體驗或氛圍（例如：安靜的、適合家庭的、浪漫的等）
        6. 最佳搜索關鍵詞（為Google Maps搜索優化的2-3個關鍵詞）
        
        請使用以下JSON格式回答，確保它是有效的JSON：
        {{
            "cuisine_type": "菜系或食物類型",
            "specific_foods": ["食物1", "食物2", ...],
            "price_range": "價格範圍",
            "dietary_requirements": ["需求1", "需求2", ...],
            "dining_experience": ["體驗1", "體驗2", ...],
            "search_keywords": ["關鍵詞1", "關鍵詞2", "關鍵詞3"]
        }}
        
        如果用戶的輸入中沒有提到某個類別的信息，請將該字段設置為空列表或空字符串。
        """
        
        # API請求數據
        data = {
            "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "prompt": prompt,
            "max_tokens": 800,
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        # 發送請求
        response = requests.post(
            "https://api.together.xyz/v1/completions",
            headers=headers,
            json=data
        )
        
        # 檢查響應
        if response.status_code == 200:
            result = response.json()
            answer_text = result.get("choices", [{}])[0].get("text", "").strip()
            
            # 解析JSON
            try:
                # 使用正則表達式找到JSON部分
                json_match = re.search(r'\{[\s\S]*?\}', answer_text)
                if json_match:
                    json_str = json_match.group(0)
                    
                    # 處理可能的trailing commas
                    json_str = re.sub(r',\s*}', '}', json_str)
                    json_str = re.sub(r',\s*]', ']', json_str)
                    
                    # 解析JSON
                    analysis_result = json.loads(json_str)
                    return analysis_result
                else:
                    return None
            except Exception as e:
                return {
                    "error": f"解析AI回應時發生錯誤: {str(e)}",
                    "raw_response": answer_text
                }
        else:
            return {
                "error": f"AI服務暫時不可用 (錯誤碼: {response.status_code})"
            }
            
    except Exception as e:
        return {
            "error": f"處理請求時發生錯誤: {str(e)}"
        }

def search_restaurants_by_keywords(ai_analysis):
    """使用AI分析結果在Google Maps上搜索餐廳"""
    # 獲取當前數據庫中的餐廳作為結果
    base_query = Restaurant.objects.filter(is_active=True)
    results = []
    
    # 如果AI分析有錯誤，返回空列表
    if ai_analysis.get('error'):
        return []
    
    # 提取搜索關鍵詞
    search_keywords = ai_analysis.get('search_keywords', [])
    cuisine_type = ai_analysis.get('cuisine_type', '')
    specific_foods = ai_analysis.get('specific_foods', [])
    
    # 首先嘗試從本地數據庫獲取匹配餐廳
    local_results = search_local_restaurants(base_query, cuisine_type, specific_foods, search_keywords)
    
    # 如果本地數據庫有足夠的結果，使用這些結果
    if len(local_results) >= 3:
        return local_results
    
    # 否則，嘗試使用Google Places API獲取更多結果
    google_results = search_google_places(ai_analysis)
    
    # 合併本地和Google搜索結果，優先顯示本地結果
    seen_names = set(restaurant.name for restaurant in local_results)
    
    for restaurant in google_results:
        if restaurant.get('name') not in seen_names:
            # 獲取 Google 餐廳照片網址（如果有）
            photo_url = None
            if restaurant.get('photos') and len(restaurant.get('photos')) > 0:
                photo_reference = restaurant.get('photos')[0].get('photo_reference')
                if photo_reference:
                    photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_reference}&key={settings.GOOGLE_MAPS_API_KEY}"
            
            # 創建臨時餐廳對象以與模板兼容
            temp_restaurant = {
                'name': restaurant.get('name', ''),
                'address': restaurant.get('vicinity', ''),
                'lat': restaurant.get('geometry', {}).get('location', {}).get('lat'),
                'lng': restaurant.get('geometry', {}).get('location', {}).get('lng'),
                'rating': restaurant.get('rating', 0),
                'from_google': True,  # 標記為來自Google
                'place_id': restaurant.get('place_id', ''),
                'image_url': photo_url  # 添加照片URL
            }
            results.append(temp_restaurant)
            seen_names.add(restaurant.get('name', ''))
    
    # 添加本地結果
    for restaurant in local_results:
        # 創建與Google結果格式一致的本地餐廳對象
        local_restaurant = {
            'name': restaurant.name,
            'address': restaurant.address,
            'lat': restaurant.lat,
            'lng': restaurant.lng,
            'rating': restaurant.reviews.aggregate(Avg('rating')).get('rating__avg', 0) or 0,
            'from_google': False,
            'id': restaurant.id,
            'image': restaurant.image if restaurant.image else None,
            'image_url': restaurant.image.url if restaurant.image and restaurant.image.name else None
        }
        results.insert(0, local_restaurant)
    
    return results

def search_local_restaurants(query, cuisine_type, specific_foods, search_keywords):
    """從本地數據庫搜索餐廳"""
    if cuisine_type:
        # 嘗試匹配餐廳類別
        query = query.filter(categories__name__icontains=cuisine_type)
    
    # 嘗試匹配菜單項目
    if specific_foods:
        food_query = None
        for food in specific_foods:
            if food_query is None:
                food_query = Q(menu_items__name__icontains=food)
            else:
                food_query |= Q(menu_items__name__icontains=food)
        
        if food_query:
            query = query.filter(food_query)
    
    # 使用搜索關鍵詞
    if search_keywords:
        keyword_query = None
        for keyword in search_keywords:
            if keyword_query is None:
                keyword_query = Q(name__icontains=keyword) | Q(description__icontains=keyword)
            else:
                keyword_query |= Q(name__icontains=keyword) | Q(description__icontains=keyword)
        
        if keyword_query:
            query = query.filter(keyword_query)
    
    # 去重
    return query.distinct()

def search_google_places(ai_analysis):
    """使用Google Places API搜索餐廳"""
    # 獲取API密鑰
    api_key = settings.GOOGLE_MAPS_API_KEY
    if not api_key:
        return []
    
    # 構建搜索關鍵詞
    search_keywords = ai_analysis.get('search_keywords', [])
    if not search_keywords and ai_analysis.get('cuisine_type'):
        search_keywords = [ai_analysis.get('cuisine_type')]
    
    if not search_keywords and ai_analysis.get('specific_foods'):
        search_keywords = ai_analysis.get('specific_foods')[:2]
    
    if not search_keywords:
        return []
    
    # 使用第一個關鍵詞作為主要搜索詞
    keyword = search_keywords[0]
    
    try:
        # 使用固定位置（可以改為用戶位置）
        # 這裡使用國立中央大學附近作為搜索中心點
        location = "24.9681567,121.1927952"  # 國立中央大學座標
        radius = 5000  # 搜索半徑（米）
        
        # 構建API URL
        url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={location}&radius={radius}&keyword={keyword}&type=restaurant&key={api_key}"
        
        # 發送請求
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            places = data.get('results', [])
            return places[:10]  # 限制結果數量
        else:
            return []
    except Exception as e:
        return []
