from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from food_analysis.models import PersonalFoodRecord
from restaurants.models import Restaurant

class Friendship(models.Model):
    """好友關係模型"""
    STATUS_CHOICES = [
        ('pending', '待確認'),
        ('accepted', '已接受'),
        ('blocked', '已封鎖'),
    ]
    
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('from_user', 'to_user')
        
    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username} ({self.status})"

class SocialPost(models.Model):
    """社交動態模型"""
    POST_TYPES = [
        ('food_record', '飲食記錄'),
        ('restaurant_review', '餐廳評價'),
        ('achievement', '成就分享'),
        ('text', '文字動態'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    post_type = models.CharField(max_length=20, choices=POST_TYPES)
    content = models.TextField()
    image = models.ImageField(upload_to='social_posts/', blank=True, null=True)
    
    # 關聯的記錄
    food_record = models.ForeignKey(PersonalFoodRecord, on_delete=models.CASCADE, blank=True, null=True)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, blank=True, null=True)
    
    # 隱私設定
    is_public = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.user.username} - {self.get_post_type_display()}"

class PostLike(models.Model):
    """動態點讚模型"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(SocialPost, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'post')
        
    def __str__(self):
        return f"{self.user.username} 讚了 {self.post.user.username} 的動態"

class PostComment(models.Model):
    """動態評論模型"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(SocialPost, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        
    def __str__(self):
        return f"{self.user.username} 評論了 {self.post.user.username} 的動態"

class FoodGroup(models.Model):
    """飲食群組模型"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='group_images/', blank=True, null=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    members = models.ManyToManyField(User, through='GroupMembership', related_name='joined_groups')
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class GroupMembership(models.Model):
    """群組成員關係模型"""
    ROLE_CHOICES = [
        ('admin', '管理員'),
        ('moderator', '版主'),
        ('member', '成員'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(FoodGroup, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'group')
        
    def __str__(self):
        return f"{self.user.username} - {self.group.name} ({self.get_role_display()})"

class GroupChallenge(models.Model):
    """群組挑戰模型"""
    CHALLENGE_TYPES = [
        ('calorie_limit', '熱量控制'),
        ('protein_goal', '蛋白質目標'),
        ('vegetarian_days', '素食天數'),
        ('water_intake', '飲水量'),
        ('exercise_calories', '運動消耗'),
    ]
    
    group = models.ForeignKey(FoodGroup, on_delete=models.CASCADE, related_name='challenges')
    title = models.CharField(max_length=100)
    description = models.TextField()
    challenge_type = models.CharField(max_length=20, choices=CHALLENGE_TYPES)
    target_value = models.FloatField()  # 目標值
    start_date = models.DateField()
    end_date = models.DateField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    participants = models.ManyToManyField(User, through='ChallengeParticipation', related_name='challenges')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.group.name} - {self.title}"

class ChallengeParticipation(models.Model):
    """挑戰參與記錄模型"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    challenge = models.ForeignKey(GroupChallenge, on_delete=models.CASCADE)
    current_progress = models.FloatField(default=0)
    is_completed = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        unique_together = ('user', 'challenge')
        
    def __str__(self):
        return f"{self.user.username} - {self.challenge.title}"

class UserProfile(models.Model):
    """用戶社交資料模型"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='social_profile')
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    location = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField(blank=True, null=True)
    
    # 隱私設定
    show_email = models.BooleanField(default=False)
    show_location = models.BooleanField(default=True)
    show_birth_date = models.BooleanField(default=False)
    
    # 統計數據
    total_posts = models.IntegerField(default=0)
    total_likes_received = models.IntegerField(default=0)
    total_friends = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} 的社交資料"

class Notification(models.Model):
    """通知模型"""
    NOTIFICATION_TYPES = [
        ('friend_request', '好友請求'),
        ('friend_accepted', '好友接受'),
        ('post_like', '動態點讚'),
        ('post_comment', '動態評論'),
        ('group_invite', '群組邀請'),
        ('challenge_invite', '挑戰邀請'),
        ('achievement', '成就獲得'),
    ]
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications', blank=True, null=True)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=100)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    
    # 關聯對象
    related_post = models.ForeignKey(SocialPost, on_delete=models.CASCADE, blank=True, null=True)
    related_group = models.ForeignKey(FoodGroup, on_delete=models.CASCADE, blank=True, null=True)
    related_challenge = models.ForeignKey(GroupChallenge, on_delete=models.CASCADE, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.recipient.username} - {self.title}"
