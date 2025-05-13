from django.urls import path
from . import views

urlpatterns = [
    path('new/', views.checkin_create, name='checkin_create'),
    path('<int:pk>/', views.checkin_detail, name='checkin_detail'),
    path('<int:pk>/edit/', views.checkin_update, name='checkin_update'),
    path('<int:pk>/delete/', views.checkin_delete, name='checkin_delete'),
    path('list/', views.checkin_list, name='checkin_list'),
    path('calendar/', views.checkin_calendar, name='checkin_calendar'),
] 