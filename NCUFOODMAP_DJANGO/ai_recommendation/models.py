from django.db import models

# Create your models here.

class AIRecommendation(models.Model):
    query = models.CharField(max_length=255)
    store_type = models.CharField(max_length=100)
    store_name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()
    ai_analysis = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.store_type}: {self.store_name}"
