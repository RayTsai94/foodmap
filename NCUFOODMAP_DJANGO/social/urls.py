from django.urls import path
from . import views

app_name = 'social'

urlpatterns = [
    # 社交動態
    path('', views.social_feed, name='feed'),
    path('like/<int:post_id>/', views.toggle_like, name='toggle_like'),
    path('like_post/<int:post_id>/', views.like_post, name='like_post'),
    path('comment/<int:post_id>/', views.add_comment, name='add_comment'),
    
    # 好友系統
    path('friends/', views.friends_list, name='friends'),
    path('friends/request/<int:user_id>/', views.send_friend_request, name='send_friend_request'),
    path('friends/respond/<int:friendship_id>/<str:action>/', views.respond_friend_request, name='respond_friend_request'),
    
    # 群組功能
    path('groups/', views.groups_list, name='groups'),
    path('groups/<int:group_id>/', views.group_detail, name='group_detail'),
    path('groups/<int:group_id>/join/', views.join_group, name='join_group'),
    path('groups/<int:group_id>/delete/', views.delete_group, name='delete_group'),
    path('groups/<int:group_id>/leave/', views.leave_group, name='leave_group'),
    
    # 成員管理
    path('membership/<int:membership_id>/change-role/', views.change_member_role, name='change_member_role'),
    path('membership/<int:membership_id>/remove/', views.remove_member, name='remove_member'),
    
    # 用戶資料
    path('profile/', views.user_profile, name='profile'),
    path('profile/<int:user_id>/', views.user_profile, name='user_profile'),
    
    # 通知
    path('notifications/', views.notifications, name='notifications'),
    
    # 聊天功能
    path('chat/', views.chat_list, name='chat_list'),
    path('chat/<int:room_id>/', views.chat_room, name='chat_room'),
    path('chat/start/<int:user_id>/', views.start_private_chat, name='start_private_chat'),
    path('chat/create-group/', views.create_group_chat, name='create_group_chat'),
    path('chat/message/<int:message_id>/delete/', views.delete_message, name='delete_message'),
    path('chat/<int:room_id>/leave/', views.leave_chat_room, name='leave_chat_room'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
] 