from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('restaurants/', views.restaurant_list, name='restaurant_list'),
    path('search_suggestions/', views.search_suggestions, name='search_suggestions'),
    path('restaurants/<int:pk>/', views.restaurant_detail, name='restaurant_detail'),
    path('menu-items/<int:pk>/', views.menu_item_detail, name='menu_item_detail'),
    path('map/', views.map_view, name='map'),
    path('delete-account/', views.delete_account, name='delete_account'),
] 