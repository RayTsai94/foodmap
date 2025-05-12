from django.shortcuts import render, redirect
import redis
from django.conf import settings

def home(request):
    return render(request, "index.html")

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        request.session['user'] = username
        return redirect('/')
    return render(request, 'login.html')

def logout_view(request):
    request.session.flush()
    return redirect('/')

def calendar_page(request):
    return render(request, "calendar.html")

# def checkin_new(request):
#     return render(request, "checkin/checkin_form.html")  # 已移除，避免衝突

def restaurant_rank_view(request):
    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    top10 = r.zrevrange('restaurant_rank', 0, 9, withscores=True)
    # 轉換成 [(id, 分數)] 格式
    restaurant_ranks = [(item.decode('utf-8'), int(score)) for item, score in top10]
    return render(request, 'restaurant_rank.html', {'restaurant_ranks': restaurant_ranks})

def user_rank_view(request):
    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    top10 = r.zrevrange('user_rank', 0, 9, withscores=True)
    user_ranks = [(item.decode('utf-8'), int(score)) for item, score in top10]
    return render(request, 'user_rank.html', {'user_ranks': user_ranks})