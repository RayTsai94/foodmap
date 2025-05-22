from django.urls import path
from . import views

app_name = 'ai_recommendation'
 
urlpatterns = [
    path('', views.index, name='index'),
    path('get_recommendation/', views.get_recommendation, name='get_recommendation'),
] 