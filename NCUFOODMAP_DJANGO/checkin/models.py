from django.db import models
from django.contrib.auth.models import User

class Checkin(models.Model):
    MOOD_CHOICES = [
        ('happy', '開心'),
        ('soso', '普通'),
        ('sad', '難過'),
        ('angry', '生氣'),
        ('surprised', '驚訝'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='checkins')
    date = models.DateField(verbose_name='用餐日期')
    restaurant_name = models.CharField(max_length=100, verbose_name='餐廳名稱')
    item = models.CharField(max_length=100, verbose_name='品項')
    price = models.DecimalField(max_digits=6, decimal_places=0, verbose_name='價格')
    rating = models.PositiveSmallIntegerField(verbose_name='評分')
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES, verbose_name='心情標籤')
    comment = models.TextField(blank=True, verbose_name='心得')
    photo = models.ImageField(upload_to='checkin_photos/', blank=True, null=True, verbose_name='照片')
    created_at = models.DateTimeField(auto_now_add=True)
    latitude = models.FloatField(blank=True, null=True, verbose_name='緯度')
    longitude = models.FloatField(blank=True, null=True, verbose_name='經度')

    def __str__(self):
        return f'{self.restaurant_name} - {self.date} ({self.user.username})'

    def get_mood_display(self):
        return dict(self.MOOD_CHOICES).get(self.mood, self.mood) 