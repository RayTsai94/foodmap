from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Avg, Sum
from restaurants.models import MenuItem, Restaurant
from .models import NutritionInfo, Ingredient, FoodPreference
import random

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
