from django.urls import path
from . import views

urlpatterns = [
    path('', views.nutrition_dashboard, name='nutrition_dashboard'),
    path('preferences/', views.dietary_preferences, name='dietary_preferences'),
    path('allergens/', views.allergen_info, name='allergen_info'),
    path('ingredients/', views.ingredient_analysis, name='ingredient_analysis'),
    path('ai-advisor/', views.ai_nutrition_advisor, name='ai_advisor'),
    path('my-food-records/', views.user_food_record, name='user_food_record'),
    path('ai-food-analysis/', views.ai_food_analysis, name='ai_food_analysis'),
    path('save-analysis/', views.save_analysis_to_record, name='save_analysis_to_record'),
    path('delete-food-record/<int:record_id>/', views.delete_food_record, name='delete_food_record'),
    path('ai-restaurant-matcher/', views.ai_restaurant_matcher, name='ai_restaurant_matcher'),
] 