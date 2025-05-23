from django.urls import path
from . import views

urlpatterns = [
    path('', views.article_list, name='article_list'),
    path('create/', views.article_create, name='article_create'),
    path('<int:article_id>/', views.article_detail, name='article_detail'),
    path('<int:article_id>/edit/', views.article_edit, name='article_edit'),
    path('<int:article_id>/delete/', views.article_delete, name='article_delete'),
    path('<int:article_id>/comment/', views.article_comment, name='article_comment'),
    path('<int:article_id>/comment/<int:comment_id>/delete/', views.article_comment_delete, name='article_comment_delete'),
] 