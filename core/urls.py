from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('calendar/', views.calendar_page, name='calendar'),
    path('checkin/new/', views.checkin_new, name='checkin_new'),
]
