from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Avg, Q, Count
from django.core.paginator import Paginator
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from .models import Restaurant, Category, Review, MenuItem
from .forms import ReviewForm, RestaurantFilterForm
from django.http import JsonResponse
import json


def home(request):
    """首頁視圖，顯示熱門餐廳和分類"""
    # 獲取評分最高的5家餐廳
    top_restaurants = Restaurant.objects.filter(is_active=True).annotate(
        avg_rating=Avg('reviews__rating')
    ).order_by('-avg_rating')[:5]
    
    # 獲取有餐廳的分類
    categories = Category.objects.annotate(
        restaurant_count=Count('restaurants')
    ).filter(restaurant_count__gt=0)
    
    return render(request, 'restaurants/home.html', {
        'top_restaurants': top_restaurants,
        'categories': categories,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
    })

def restaurant_list(request):
    """餐廳列表視圖，支持分類、評分、關鍵字過濾與分頁"""
    restaurants = Restaurant.objects.filter(is_active=True)

    # 過濾表單
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
        # 關鍵字搜尋（名稱、地址、分類）
        name_or_address = filter_form.cleaned_data.get('name_or_address')
        if name_or_address:
            restaurants = restaurants.filter(
                Q(name__icontains=name_or_address) |
                Q(address__icontains=name_or_address) |
                Q(categories__name__icontains=name_or_address)
            ).distinct()

    # 排序（避免分頁警告）
    restaurants = restaurants.order_by('id')

    # 分頁
    paginator = Paginator(restaurants, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 傳遞「所有符合條件」的餐廳給地圖
    all_restaurant_json = json.dumps([
        {
            'id': r.id,
            'name': r.name,
            'address': r.address,
            'lat': r.lat,
            'lng': r.lng,
            'categories': ', '.join([c.name for c in r.categories.all()]),
            'image': f"/static/restaurant_images/{r.image}" if r.image else '/static/img/default-restaurant.jpg',
            'url': f"/restaurants/{r.id}/"
        }
        for r in restaurants if r.lat and r.lng
    ])

    return render(request, 'restaurants/restaurant_list.html', {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'restaurant_json': all_restaurant_json,  # 這裡改成 all_restaurant_json
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

def map_view(request):
    """地圖視圖，顯示餐廳位置"""
    restaurants = Restaurant.objects.filter(is_active=True, lat__isnull=False, lng__isnull=False)
    
    return render(request, 'restaurants/map.html', {
        'restaurants': restaurants,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
    })

def search_suggestions(request):
    q = request.GET.get('q', '')
    suggestions = []
    if q:
        restaurants = Restaurant.objects.filter(name__icontains=q)[:10]
        for r in restaurants:
            suggestions.append({
                'name': r.name,
                'address': r.address,
                'rating': r.reviews.aggregate(Avg('rating'))['rating__avg'] or 0,
            })
    return JsonResponse({'suggestions': suggestions})

@login_required
def delete_account(request):
    """刪除用戶帳戶"""
    if request.method == 'POST':
        user = request.user
        # 登出用戶
        logout(request)
        # 刪除用戶
        user.delete()
        messages.success(request, '您的帳戶已經成功刪除。')
        return redirect('home')
    # GET 請求顯示確認頁面
    return render(request, 'restaurants/confirm_delete_account.html')
