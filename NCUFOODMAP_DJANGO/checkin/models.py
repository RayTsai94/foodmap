from django.db import models
from django.contrib.auth.models import User

class Checkin(models.Model):
    MOOD_CHOICES = [
        ("happy", "開心"),
        ("satisfied", "滿足"),
        ("neutral", "普通"),
        ("sad", "難過"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="checkins")
    date = models.DateField(verbose_name="用餐日期")
    restaurant_name = models.CharField(max_length=100, verbose_name="餐廳名稱")
    item = models.CharField(max_length=100, verbose_name="品項")
    price = models.PositiveIntegerField(verbose_name="價格")
    rating = models.PositiveSmallIntegerField(verbose_name="評分")
    mood = models.CharField(max_length=10, choices=MOOD_CHOICES, verbose_name="心情標籤")
    comment = models.TextField(blank=True, verbose_name="心得")
    photo = models.ImageField(upload_to="checkin_photos/", blank=True, null=True, verbose_name="照片")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.restaurant_name} @ {self.date}" 