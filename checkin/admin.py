from django.contrib import admin
from .models import Checkin

@admin.register(Checkin)
class CheckinAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'restaurant', 'rating']
    list_filter = ['date', 'rating']
    search_fields = ['restaurant', 'comment']
