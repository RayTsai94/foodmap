from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Checkin
from .forms import CheckinForm
from django.core.paginator import Paginator
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Avg, Count
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from django.core.cache import cache
import requests
import json
from django.conf import settings
from django.http import JsonResponse

@login_required
def render_map_data(request):
    checkins = Checkin.objects.filter(user=request.user)
    data = [
        {
            'latitude': c.latitude,
            'longitude': c.longitude,
            'restaurant_name': c.restaurant_name,
            'item': c.item,
            'price': c.price,
            'comment': c.comment,
        }
        for c in checkins if c.latitude and c.longitude
    ]
    return JsonResponse(data, safe=False, encoder=DjangoJSONEncoder)

@login_required
def checkin_list(request):
    query = request.GET.get('q', '')
    sort = request.GET.get('sort', '-date')
    checkins = Checkin.objects.filter(user=request.user)
    if query:
        checkins = checkins.filter(
            models.Q(restaurant_name__icontains=query) |
            models.Q(item__icontains=query) |
            models.Q(comment__icontains=query)
        )
    # 排序
    if sort in ['date', '-date', 'rating', '-rating']:
        checkins = checkins.order_by(sort)
    else:
        checkins = checkins.order_by('-date')
    # 分頁
    paginator = Paginator(checkins, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # 統計
    now = timezone.now()
    month_checkins = checkins.filter(date__year=now.year, date__month=now.month)
    month_count = month_checkins.count()
    avg_rating = month_checkins.aggregate(avg=Avg('rating'))['avg']
    context = {
        'page_obj': page_obj,
        'query': query,
        'sort': sort,
        'month_count': month_count,
        'avg_rating': avg_rating,
    }
    return render(request, 'checkin/checkin_list.html', context)

@login_required
def checkin_detail(request, pk):
    checkin = get_object_or_404(Checkin, pk=pk, user=request.user)
    return render(request, 'checkin/checkin_detail.html', {'checkin': checkin})

def get_lat_lng(address):
    api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', None)
    if not api_key:
        return None, None
    url = f'https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}'
    try:
        resp = requests.get(url)
        data = resp.json()
        if data['status'] == 'OK':
            location = data['results'][0]['geometry']['location']
            return location['lat'], location['lng']
    except Exception:
        pass
    return None, None

@login_required
def checkin_create(request):
    if request.method == 'POST':
        form = CheckinForm(request.POST, request.FILES)
        if form.is_valid():
            checkin = form.save(commit=False)
            checkin.user = request.user
            # 自動查詢經緯度
            lat, lng = get_lat_lng(checkin.restaurant_name)
            checkin.latitude = lat
            checkin.longitude = lng
            checkin.save()
            messages.success(request, '打卡成功！')
            return redirect('checkin_list')
    else:
        form = CheckinForm()
    return render(request, 'checkin/checkin_form.html', {'form': form})

@login_required
def checkin_update(request, pk):
    checkin = get_object_or_404(Checkin, pk=pk, user=request.user)
    if request.method == 'POST':
        form = CheckinForm(request.POST, request.FILES, instance=checkin)
        if form.is_valid():
            checkin = form.save(commit=False)
            # 自動查詢經緯度（若餐廳名稱有變動）
            lat, lng = get_lat_lng(checkin.restaurant_name)
            checkin.latitude = lat
            checkin.longitude = lng
            checkin.save()
            messages.success(request, '打卡紀錄已更新！')
            return redirect('checkin_detail', pk=checkin.pk)
    else:
        form = CheckinForm(instance=checkin)
    return render(request, 'checkin/checkin_form.html', {'form': form})

@login_required
def checkin_delete(request, pk):
    checkin = get_object_or_404(Checkin, pk=pk, user=request.user)
    if request.method == 'POST':
        checkin.delete()
        messages.success(request, '打卡紀錄已刪除！')
        return redirect('checkin_list')
    return render(request, 'checkin/checkin_confirm_delete.html', {'checkin': checkin})
# 可能需要改一下
@login_required
def user_ranking(request):
    from django.db.models import Count
    from django.utils import timezone
    now = timezone.now()
    cache_key = f"user_ranking_{now.year}_{now.month}"
    data = cache.get(cache_key)
    if not data:
        user_ranking = User.objects.annotate(
            checkin_count=Count('checkins', filter=models.Q(checkins__date__year=now.year, checkins__date__month=now.month))
        ).order_by('-checkin_count')[:10]
        data = list(user_ranking)
        cache.set(cache_key, data, 300)
    else:
        user_ranking = data
    return render(request, 'checkin/user_ranking.html', {'user_ranking': user_ranking})

@login_required
def restaurant_ranking(request):
    from django.db.models import Count, Avg
    from django.utils import timezone
    now = timezone.now()
    cache_key = f"restaurant_ranking_{now.year}_{now.month}"
    data = cache.get(cache_key)
    if not data:
        top_rated = Checkin.objects.filter(
            date__year=now.year,
            date__month=now.month,
            rating__gte=1  # 只計算有效分數
        ).values('restaurant_name').annotate(
            avg_rating=Avg('rating'), count=Count('id')
        ).filter(count__gte=2).order_by('-avg_rating')[:10]
        data = list(top_rated)
        cache.set(cache_key, data, 300)
    else:
        top_rated = data
    return render(request, 'checkin/restaurant_ranking.html', {'top_rated': top_rated})

@login_required
def ranking(request):
    from django.db.models import Count, Avg
    from django.utils import timezone
    now = timezone.now()
    cache_key = f"ranking_{now.year}_{now.month}"
    data = cache.get(cache_key)
    if not data:
        # 本月打卡最多的用戶
        user_ranking = User.objects.annotate(
            checkin_count=Count('checkins', filter=models.Q(checkins__date__year=now.year, checkins__date__month=now.month))
        ).order_by('-checkin_count')[:10]
        # 打卡最多的餐廳
        restaurant_ranking = Checkin.objects.filter(date__year=now.year, date__month=now.month)
        restaurant_ranking = restaurant_ranking.values('restaurant_name').annotate(
            count=Count('id'), avg_rating=Avg('rating')
        ).order_by('-count')[:10]
        # 評分最高的餐廳（至少2筆打卡）
        top_rated = Checkin.objects.filter(date__year=now.year, date__month=now.month)
        top_rated = top_rated.values('restaurant_name').annotate(
            avg_rating=Avg('rating'), count=Count('id')
        ).filter(count__gte=2).order_by('-avg_rating')[:10]
        data = {
            'user_ranking': list(user_ranking),
            'restaurant_ranking': list(restaurant_ranking),
            'top_rated': list(top_rated),
        }
        cache.set(cache_key, data, 300)  # 快取 5 分鐘
    else:
        user_ranking = data['user_ranking']
        restaurant_ranking = data['restaurant_ranking']
        top_rated = data['top_rated']
    return render(request, 'checkin/ranking.html', {
        'user_ranking': user_ranking,
        'restaurant_ranking': restaurant_ranking,
        'top_rated': top_rated,
    })

@login_required
def my_checkin_points(request):
    checkins = Checkin.objects.filter(user=request.user, latitude__isnull=False, longitude__isnull=False)
    data = [
        {
            'restaurant_name': c.restaurant_name,
            'date': c.date.strftime('%Y-%m-%d'),
            'item': c.item,
            'comment': c.comment,
            'latitude': c.latitude,
            'longitude': c.longitude,
        }
        for c in checkins
    ]
    return JsonResponse({'points': data}) 