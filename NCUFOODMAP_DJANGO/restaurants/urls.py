from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_redirect, name='home'),
    path('restaurants/', views.restaurant_list, name='restaurant_list'),
    path('restaurants/<int:pk>/', views.restaurant_detail, name='restaurant_detail'),
    path('menu-items/<int:pk>/', views.menu_item_detail, name='menu_item_detail'),
    path('map/', views.map_view, name='map'),
] 