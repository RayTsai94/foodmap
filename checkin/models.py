from django.db import models
from django.contrib.auth.models import User

class Checkin(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    restaurant = models.CharField(max_length=100)
    comment = models.TextField(blank=True)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], default=3)
    image = models.ImageField(upload_to='checkin_images/', null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.date} - {self.restaurant}"
