from django.urls import path
from . import views

urlpatterns = [
    path('new/', views.new_checkin, name='new_checkin'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('', views.checkin_form, name='checkin_form'),
    path('checkin/<int:checkin_id>/', views.checkin_detail, name='checkin_detail'),
    path('checkin/<int:checkin_id>/edit/', views.edit_checkin, name='edit_checkin'),
    path('checkin/<int:checkin_id>/delete/', views.delete_checkin, name='delete_checkin'),
]
