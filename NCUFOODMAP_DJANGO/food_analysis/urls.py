from django.urls import path
from . import views

urlpatterns = [
    path('', views.nutrition_dashboard, name='nutrition_dashboard'),
    path('preferences/', views.dietary_preferences, name='dietary_preferences'),
    path('allergens/', views.allergen_info, name='allergen_info'),
    path('ingredients/', views.ingredient_analysis, name='ingredient_analysis'),
    path('ai-advisor/', views.ai_nutrition_advisor, name='ai_advisor'),
] 