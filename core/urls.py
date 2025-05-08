from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('calendar/', views.calendar_page, name='calendar'),
    # path('checkin/new/', views.checkin_new, name='checkin_new'), # 已移除，避免衝突
    path('restaurant-rank/', views.restaurant_rank_view, name='restaurant_rank'),
    path('user-rank/', views.user_rank_view, name='user_rank'),
]
