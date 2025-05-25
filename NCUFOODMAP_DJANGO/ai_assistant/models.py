from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class ChatHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100)  # 用於未登入用戶
    message = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    current_page = models.CharField(max_length=200)  # 記錄用戶在哪個頁面發起的對話

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username if self.user else 'Anonymous'} - {self.created_at}"
