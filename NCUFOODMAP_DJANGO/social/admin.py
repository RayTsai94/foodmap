from django.contrib import admin
from .models import (
    Friendship, SocialPost, PostLike, PostComment, 
    FoodGroup, GroupMembership, GroupChallenge, ChallengeParticipation,
    UserProfile, Notification
)

@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ['from_user', 'to_user', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['from_user__username', 'to_user__username']

@admin.register(SocialPost)
class SocialPostAdmin(admin.ModelAdmin):
    list_display = ['user', 'post_type', 'content_preview', 'is_public', 'created_at']
    list_filter = ['post_type', 'is_public', 'created_at']
    search_fields = ['user__username', 'content']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = '內容預覽'

@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'post__content']

@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'content_preview', 'parent', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'content']
    
    def content_preview(self, obj):
        return obj.content[:30] + '...' if len(obj.content) > 30 else obj.content
    content_preview.short_description = '評論預覽'

@admin.register(FoodGroup)
class FoodGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'creator', 'is_public', 'member_count', 'created_at']
    list_filter = ['is_public', 'created_at']
    search_fields = ['name', 'description', 'creator__username']
    
    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = '成員數量'

@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'group', 'role', 'joined_at']
    list_filter = ['role', 'joined_at']
    search_fields = ['user__username', 'group__name']

@admin.register(GroupChallenge)
class GroupChallengeAdmin(admin.ModelAdmin):
    list_display = ['title', 'group', 'challenge_type', 'target_value', 'start_date', 'end_date', 'created_by']
    list_filter = ['challenge_type', 'start_date', 'end_date']
    search_fields = ['title', 'description', 'group__name']

@admin.register(ChallengeParticipation)
class ChallengeParticipationAdmin(admin.ModelAdmin):
    list_display = ['user', 'challenge', 'current_progress', 'is_completed', 'joined_at']
    list_filter = ['is_completed', 'joined_at']
    search_fields = ['user__username', 'challenge__title']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'location', 'total_posts', 'total_likes_received', 'total_friends', 'created_at']
    list_filter = ['show_email', 'show_location', 'show_birth_date', 'created_at']
    search_fields = ['user__username', 'bio', 'location']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'sender', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['recipient__username', 'sender__username', 'title', 'message']
