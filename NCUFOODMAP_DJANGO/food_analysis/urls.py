from django.urls import path
from . import views

urlpatterns = [
    path('ai-advisor/', views.ai_nutrition_advisor, name='ai_advisor'),
    path('ai-food-analysis/', views.ai_food_analysis, name='ai_food_analysis'),
    path('my-diary/', views.personal_food_diary, name='personal_food_diary'),
    path('my-dashboard/', views.personal_nutrition_dashboard, name='personal_nutrition_dashboard'),
] 