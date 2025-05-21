from django.urls import path
from . import views

urlpatterns = [
    path('', views.checkin_list, name='checkin_list'),
    path('json/', views.render_map_data, name='checkin_map_json'),
    path('new/', views.checkin_create, name='checkin_create'),
    path('<int:pk>/', views.checkin_detail, name='checkin_detail'),
    path('<int:pk>/edit/', views.checkin_update, name='checkin_update'),
    path('<int:pk>/delete/', views.checkin_delete, name='checkin_delete'),
    path('ranking/', views.ranking, name='ranking'),
    path('user_ranking/', views.user_ranking, name='user_ranking'),
    path('restaurant_ranking/', views.restaurant_ranking, name='restaurant_ranking'),
    path('my_points/', views.my_checkin_points, name='my_checkin_points'),
] 