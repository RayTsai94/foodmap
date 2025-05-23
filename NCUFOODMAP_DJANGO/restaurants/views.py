from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Avg, Q
from django.core.paginator import Paginator
from django.conf import settings
from django.http import JsonResponse
from .models import Restaurant, Category, Review, MenuItem
from .forms import ReviewForm, RestaurantFilterForm


def home(request):
    """首頁視圖，顯示熱門餐廳和分類"""
    # 獲取評分最高的5家餐廳
    top_restaurants = Restaurant.objects.filter(is_active=True).annotate(
        avg_rating=Avg('reviews__rating')
    ).order_by('-avg_rating')[:5]
    
    # 獲取所有分類
    categories = Category.objects.all()
    
    return render(request, 'restaurants/home.html', {
        'top_restaurants': top_restaurants,
        'categories': categories,
    })

def restaurant_list(request):
    """餐廳列表視圖，支持過濾和分頁"""
    restaurants = Restaurant.objects.filter(is_active=True)
    
    # 處理過濾
    filter_form = RestaurantFilterForm(request.GET)
    if filter_form.is_valid():
        # 分類過濾
        category = filter_form.cleaned_data.get('category')
        if category:
            restaurants = restaurants.filter(categories=category)
        
        # 評分過濾
        min_rating = filter_form.cleaned_data.get('min_rating')
        if min_rating:
            restaurants = restaurants.annotate(
                avg_rating=Avg('reviews__rating')
            ).filter(avg_rating__gte=min_rating)
        
        # 關鍵字搜尋
        name_or_address = filter_form.cleaned_data.get('name_or_address')
        if name_or_address:
            restaurants = restaurants.filter(
                Q(name__icontains=name_or_address) | Q(address__icontains=name_or_address)
            )
    
    # 分頁
    paginator = Paginator(restaurants, 12)  # 每頁12個餐廳
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'restaurants/restaurant_list.html', {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
    })

def restaurant_detail(request, pk):
    """餐廳詳情視圖，顯示餐廳信息、菜單和評論"""
    restaurant = get_object_or_404(Restaurant, pk=pk, is_active=True)
    
    # 獲取菜單項
    menu_items = MenuItem.objects.filter(restaurant=restaurant, is_available=True)
    
    # 處理新評論提交
    if request.method == 'POST':
        review_form = ReviewForm(request.POST)
        if review_form.is_valid():
            new_review = review_form.save(commit=False)
            new_review.restaurant = restaurant
            new_review.save()
            messages.success(request, '謝謝您的評論！')
            return redirect('restaurant_detail', pk=restaurant.pk)
    else:
        review_form = ReviewForm()
    
    # 獲取評論
    reviews = Review.objects.filter(restaurant=restaurant).order_by('-created_at')
    
    # 計算平均評分
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    return render(request, 'restaurants/restaurant_detail.html', {
        'restaurant': restaurant,
        'menu_items': menu_items,
        'reviews': reviews,
        'review_form': review_form,
        'avg_rating': avg_rating,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
    })

def menu_item_detail(request, pk):
    """菜單項詳情視圖，顯示菜單項信息和營養信息"""
    menu_item = get_object_or_404(MenuItem, pk=pk, is_available=True)
    
    # 獲取成分信息
    ingredients = menu_item.ingredients.all().select_related('ingredient')
    
    # 獲取偏好信息
    preferences = menu_item.preferences.all().select_related('preference')
    
    # 嘗試獲取營養信息，如果存在
    try:
        nutrition = menu_item.nutrition
    except:
        nutrition = None
    
    return render(request, 'restaurants/menu_item_detail.html', {
        'menu_item': menu_item,
        'ingredients': ingredients,
        'preferences': preferences,
        'nutrition': nutrition,
    })

def search_suggestions(request):
    """AJAX端點：提供搜索建議，類似Google Maps"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:  # 至少需要2個字元才開始搜索
        return JsonResponse({'suggestions': []})
    
    # 搜索餐廳名稱、地址和分類
    restaurant_suggestions = Restaurant.objects.filter(
        Q(name__icontains=query) | Q(address__icontains=query),
        is_active=True
    ).distinct()[:8]  # 限制最多8個建議
    
    # 搜索分類
    category_suggestions = Category.objects.filter(
        name__icontains=query
    )[:3]  # 最多3個分類建議
    
    suggestions = []
    
    # 添加餐廳建議
    for restaurant in restaurant_suggestions:
        # 計算平均評分
        avg_rating = restaurant.reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        review_count = restaurant.reviews.count()
        
        # 判斷匹配類型
        match_type = "restaurant"
        if query.lower() in restaurant.name.lower():
            match_in = "name"
            highlight_text = restaurant.name
        else:
            match_in = "address" 
            highlight_text = restaurant.address
            
        suggestions.append({
            'type': match_type,
            'match_in': match_in,
            'id': restaurant.id,
            'name': restaurant.name,
            'address': restaurant.address,
            'highlight_text': highlight_text,
            'avg_rating': round(avg_rating, 1),
            'review_count': review_count,
            'categories': [cat.name for cat in restaurant.categories.all()[:2]],  # 最多顯示2個分類
            'image_url': restaurant.image.url if restaurant.image else None,
        })
    
    # 添加分類建議
    for category in category_suggestions:
        restaurant_count = category.restaurants.filter(is_active=True).count()
        suggestions.append({
            'type': 'category',
            'name': category.name,
            'restaurant_count': restaurant_count,
            'icon': category.icon or 'fas fa-utensils',
        })
    
    return JsonResponse({
        'suggestions': suggestions,
        'query': query
    })
