from django.db import models
from django.contrib.auth.models import User

class Checkin(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    restaurant = models.CharField(max_length=100)
    item = models.CharField(max_length=100, default='未填寫')
    price = models.PositiveIntegerField(default=0)
    emotion_tag = models.CharField(max_length=20, default='普通')
    comment = models.TextField(blank=True)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], default=3)
    image = models.ImageField(upload_to='checkin_images/', null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.date} - {self.restaurant}"
