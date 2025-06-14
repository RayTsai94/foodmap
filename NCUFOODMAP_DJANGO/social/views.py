from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import (
    Friendship, SocialPost, PostLike, PostComment, 
    FoodGroup, GroupMembership, GroupChallenge, ChallengeParticipation,
    UserProfile, Notification, ChatRoom, ChatParticipant, ChatMessage
)
from .forms import (
    SocialPostForm, PostCommentForm, FoodGroupForm, 
    GroupChallengeForm, UserProfileForm, FriendSearchForm
)
from food_analysis.models import PersonalFoodRecord

@login_required
def social_feed(request):
    """社交動態首頁"""
    # 獲取好友列表
    friends = Friendship.objects.filter(
        Q(from_user=request.user, status='accepted') |
        Q(to_user=request.user, status='accepted')
    ).values_list('from_user', 'to_user')
    
    friend_ids = set()
    for from_user, to_user in friends:
        friend_ids.add(from_user if from_user != request.user.id else to_user)
    friend_ids.add(request.user.id)  # 包含自己的動態
    
    # 獲取動態
    posts = SocialPost.objects.filter(
        Q(user_id__in=friend_ids, is_public=True) |
        Q(user=request.user)
    ).select_related('user', 'food_record', 'restaurant').prefetch_related('likes', 'comments')
    
    # 分頁
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_posts = paginator.get_page(page_number)
    
    # 發布動態表單
    if request.method == 'POST':
        form = SocialPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            # 更新用戶統計
            request.user.social_profile.update_statistics()
            messages.success(request, '動態發布成功！')
            return redirect('social:feed')
    else:
        form = SocialPostForm()
    
    # 獲取用戶統計
    user_stats = {
        'posts_count': request.user.social_profile.total_posts,
        'friends_count': request.user.social_profile.total_friends,
        'likes_received': request.user.social_profile.total_likes_received,
    }
    
    context = {
        'posts': page_posts,
        'form': form,
        'user_stats': user_stats,
    }
    return render(request, 'social/feed.html', context)

@login_required
def toggle_like(request, post_id):
    """切換點讚狀態"""
    if request.method == 'POST':
        post = get_object_or_404(SocialPost, id=post_id)
        like, created = PostLike.objects.get_or_create(user=request.user, post=post)
        
        if not created:
            like.delete()
            liked = False
        else:
            liked = True
            # 創建通知
            if post.user != request.user:
                Notification.objects.create(
                    recipient=post.user,
                    sender=request.user,
                    notification_type='post_like',
                    title='有人讚了你的動態',
                    message=f'{request.user.username} 讚了你的動態',
                    related_post=post
                )
        
        likes_count = post.likes.count()
        return JsonResponse({'liked': liked, 'likes_count': likes_count})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def add_comment(request, post_id):
    """添加評論"""
    if request.method == 'POST':
        post = get_object_or_404(SocialPost, id=post_id)
        form = PostCommentForm(request.POST)
        
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.post = post
            comment.save()
            
            # 創建通知
            if post.user != request.user:
                Notification.objects.create(
                    recipient=post.user,
                    sender=request.user,
                    notification_type='post_comment',
                    title='有人評論了你的動態',
                    message=f'{request.user.username} 評論了你的動態',
                    related_post=post
                )
            
            messages.success(request, '評論發布成功！')
        else:
            messages.error(request, '評論發布失敗，請檢查內容。')
    
    return redirect('social:feed')

@login_required
def friends_list(request):
    """好友列表"""
    # 已接受的好友
    friends = Friendship.objects.filter(
        Q(from_user=request.user, status='accepted') |
        Q(to_user=request.user, status='accepted')
    ).select_related('from_user', 'to_user')
    
    # 待處理的好友請求
    pending_requests = Friendship.objects.filter(
        to_user=request.user, 
        status='pending'
    ).select_related('from_user')
    
    # 已發送的好友請求
    sent_requests = Friendship.objects.filter(
        from_user=request.user, 
        status='pending'
    ).select_related('to_user')
    
    # 搜尋表單
    search_form = FriendSearchForm()
    search_results = []
    
    # 獲取所有用戶（排除自己），用於推薦好友
    all_users = User.objects.exclude(id=request.user.id).order_by('username')[:20]
    
    # 獲取已經是好友的用戶ID
    friend_ids = set()
    for friendship in friends:
        if friendship.from_user == request.user:
            friend_ids.add(friendship.to_user.id)
        else:
            friend_ids.add(friendship.from_user.id)
    
    # 獲取已發送請求的用戶ID
    sent_request_ids = set(sent_requests.values_list('to_user', flat=True))
    
    # 獲取已收到請求的用戶ID
    received_request_ids = set(pending_requests.values_list('from_user', flat=True))
    
    if request.method == 'POST':
        search_form = FriendSearchForm(request.POST)
        if search_form.is_valid():
            username = search_form.cleaned_data['username']
            search_results = User.objects.filter(
                Q(username__icontains=username) | 
                Q(first_name__icontains=username) |
                Q(last_name__icontains=username) |
                Q(email__icontains=username)
            ).exclude(id=request.user.id)[:10]
    
    context = {
        'friends': friends,
        'pending_requests': pending_requests,
        'sent_requests': sent_requests,
        'search_form': search_form,
        'search_results': search_results,
        'all_users': all_users,
        'friend_ids': friend_ids,
        'sent_request_ids': sent_request_ids,
        'received_request_ids': received_request_ids,
    }
    return render(request, 'social/friends.html', context)

@login_required
def send_friend_request(request, user_id):
    """發送好友請求"""
    to_user = get_object_or_404(User, id=user_id)
    
    if to_user == request.user:
        messages.error(request, '不能向自己發送好友請求。')
        return redirect('social:friends')
    
    # 檢查是否已經是好友或已發送請求
    existing = Friendship.objects.filter(
        Q(from_user=request.user, to_user=to_user) |
        Q(from_user=to_user, to_user=request.user)
    ).first()
    
    if existing:
        if existing.status == 'accepted':
            messages.info(request, '你們已經是好友了。')
        elif existing.status == 'pending':
            messages.info(request, '好友請求已發送，請等待對方回應。')
        else:
            messages.error(request, '無法發送好友請求。')
    else:
        Friendship.objects.create(from_user=request.user, to_user=to_user)
        
        # 創建通知
        Notification.objects.create(
            recipient=to_user,
            sender=request.user,
            notification_type='friend_request',
            title='新的好友請求',
            message=f'{request.user.username} 想要加你為好友'
        )
        
        messages.success(request, '好友請求已發送！')
    
    return redirect('social:friends')

@login_required
def respond_friend_request(request, friendship_id, action):
    """回應好友請求"""
    friendship = get_object_or_404(Friendship, id=friendship_id, to_user=request.user)
    
    if action == 'accept':
        friendship.status = 'accepted'
        friendship.save()
        
        # 創建通知
        Notification.objects.create(
            recipient=friendship.from_user,
            sender=request.user,
            notification_type='friend_accepted',
            title='好友請求已接受',
            message=f'{request.user.username} 接受了你的好友請求'
        )
        
        messages.success(request, f'已接受 {friendship.from_user.username} 的好友請求！')
    elif action == 'decline':
        friendship.delete()
        messages.info(request, '已拒絕好友請求。')
    
    return redirect('social:friends')

@login_required
def groups_list(request):
    """群組列表"""
    # 用戶加入的群組
    user_groups = FoodGroup.objects.filter(members=request.user)
    
    # 公開群組
    public_groups = FoodGroup.objects.filter(is_public=True).exclude(members=request.user)
    
    # 創建群組表單
    if request.method == 'POST':
        form = FoodGroupForm(request.POST, request.FILES)
        if form.is_valid():
            group = form.save(commit=False)
            group.creator = request.user
            group.save()
            
            # 創建者自動成為管理員
            GroupMembership.objects.create(
                user=request.user,
                group=group,
                role='admin'
            )
            
            messages.success(request, '群組創建成功！')
            return redirect('social:groups')
    else:
        form = FoodGroupForm()
    
    context = {
        'user_groups': user_groups,
        'public_groups': public_groups,
        'form': form,
    }
    return render(request, 'social/groups.html', context)

@login_required
def group_detail(request, group_id):
    """群組詳情"""
    group = get_object_or_404(FoodGroup, id=group_id)
    
    # 檢查用戶是否為群組成員
    user_membership = GroupMembership.objects.filter(user=request.user, group=group).first()
    is_member = user_membership is not None
    
    if not is_member and not group.is_public:
        messages.error(request, '你沒有權限查看此群組。')
        return redirect('social:groups')
    
    # 群組成員 - 修復查詢
    memberships = GroupMembership.objects.filter(group=group).select_related('user', 'user__social_profile')
    
    # 群組挑戰
    challenges = GroupChallenge.objects.filter(group=group).order_by('-created_at')
    
    # 用戶參與的挑戰
    user_challenges = []
    if is_member:
        user_challenges = ChallengeParticipation.objects.filter(
            user=request.user,
            challenge__in=challenges
        ).values_list('challenge', flat=True)
    
    # 群組動態
    group_posts = SocialPost.objects.filter(
        user__in=group.members.all()
    ).order_by('-created_at')[:10]
    
    context = {
        'group': group,
        'user_membership': user_membership,
        'is_member': is_member,
        'memberships': memberships,  # 添加成員列表
        'challenges': challenges,
        'user_challenges': user_challenges,
        'group_posts': group_posts,
    }
    return render(request, 'social/group_detail.html', context)

@login_required
def join_group(request, group_id):
    """加入群組"""
    group = get_object_or_404(FoodGroup, id=group_id)
    
    if not group.is_public:
        messages.error(request, '此群組不開放加入。')
        return redirect('social:groups')
    
    membership, created = GroupMembership.objects.get_or_create(
        user=request.user,
        group=group,
        defaults={'role': 'member'}
    )
    
    if created:
        messages.success(request, f'成功加入群組 {group.name}！')
    else:
        messages.info(request, '你已經是此群組的成員了。')
    
    return redirect('social:group_detail', group_id=group_id)

@login_required
def user_profile(request, user_id=None):
    """用戶資料頁面"""
    if user_id:
        profile_user = get_object_or_404(User, id=user_id)
    else:
        profile_user = request.user
    
    # 獲取或創建用戶社交資料
    social_profile, created = UserProfile.objects.get_or_create(user=profile_user)
    
    # 更新統計數據
    social_profile.update_statistics()
    
    # 用戶動態
    user_posts = SocialPost.objects.filter(user=profile_user, is_public=True).order_by('-created_at')[:10]
    
    # 好友狀態
    friendship_status = None
    if profile_user != request.user:
        friendship = Friendship.objects.filter(
            Q(from_user=request.user, to_user=profile_user) |
            Q(from_user=profile_user, to_user=request.user)
        ).first()
        if friendship:
            friendship_status = friendship.status
    
    # 編輯資料表單（僅自己可編輯）
    if request.method == 'POST' and profile_user == request.user:
        form = UserProfileForm(request.POST, request.FILES, instance=social_profile)
        if form.is_valid():
            form.save()
            messages.success(request, '資料更新成功！')
            return redirect('social:profile')
    else:
        form = UserProfileForm(instance=social_profile) if profile_user == request.user else None
    
    context = {
        'profile_user': profile_user,
        'social_profile': social_profile,
        'user_posts': user_posts,
        'friendship_status': friendship_status,
        'form': form,
        'is_own_profile': profile_user == request.user,
    }
    return render(request, 'social/profile.html', context)

@login_required
def notifications(request):
    """通知列表"""
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    
    # 標記為已讀
    if request.method == 'POST':
        notification_id = request.POST.get('notification_id')
        if notification_id:
            try:
                notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
                notification.is_read = True
                notification.save()
                return JsonResponse({'success': True})
            except Exception as e:
                import traceback
                print(f"Mark as read error: {str(e)}")
                print(traceback.format_exc())
                return JsonResponse({'success': False, 'error': f'標記失敗：{str(e)}'})
        else:
            return JsonResponse({'success': False, 'error': '缺少通知ID'})
    
    # 分頁
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_notifications = paginator.get_page(page_number)
    
    context = {
        'notifications': page_notifications,
        'unread_count': notifications.filter(is_read=False).count(),
    }
    return render(request, 'social/notifications.html', context)

@login_required
def delete_group(request, group_id):
    """刪除群組（僅創建者或管理員可操作）"""
    group = get_object_or_404(FoodGroup, id=group_id)
    
    # 檢查權限：必須是創建者或管理員
    is_creator = group.creator == request.user
    membership = GroupMembership.objects.filter(user=request.user, group=group, role='admin').first()
    is_admin = membership is not None
    
    if not (is_creator or is_admin):
        return JsonResponse({'success': False, 'error': '你沒有權限刪除此群組'})
    
    if request.method == 'POST':
        try:
            # 刪除相關的通知
            Notification.objects.filter(related_group=group).delete()
            
            # 刪除群組（會自動刪除相關的成員關係和挑戰）
            group_name = group.name
            group.delete()
            
            return JsonResponse({'success': True, 'message': f'群組 {group_name} 已成功刪除'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': '無效的請求方法'})

@login_required
def leave_group(request, group_id):
    """離開群組"""
    group = get_object_or_404(FoodGroup, id=group_id)
    
    # 檢查用戶是否為群組成員
    membership = GroupMembership.objects.filter(user=request.user, group=group).first()
    if not membership:
        return JsonResponse({'success': False, 'error': '你不是此群組的成員'})
    
    # 管理員不能直接離開群組（需要先轉移管理權或刪除群組）
    if membership.role == 'admin':
        admin_count = GroupMembership.objects.filter(group=group, role='admin').count()
        if admin_count == 1:
            return JsonResponse({'success': False, 'error': '你是唯一的管理員，請先轉移管理權或刪除群組'})
    
    if request.method == 'POST':
        try:
            # 刪除成員關係
            membership.delete()
            
            # 創建通知給其他管理員
            admin_memberships = GroupMembership.objects.filter(group=group, role='admin')
            for admin_membership in admin_memberships:
                if admin_membership.user != request.user:
                    Notification.objects.create(
                        recipient=admin_membership.user,
                        sender=request.user,
                        notification_type='group_leave',
                        title='成員離開群組',
                        message=f'{request.user.username} 離開了群組 {group.name}',
                        related_group=group
                    )
            
            return JsonResponse({'success': True, 'message': f'已成功離開群組 {group.name}'})
        except Exception as e:
            import traceback
            print(f"Leave group error: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({'success': False, 'error': f'操作失敗：{str(e)}'})
    
    return JsonResponse({'success': False, 'error': '無效的請求方法'})

@login_required
def change_member_role(request, membership_id):
    """更改成員角色"""
    membership = get_object_or_404(GroupMembership, id=membership_id)
    group = membership.group
    
    # 檢查權限：必須是管理員
    user_membership = GroupMembership.objects.filter(user=request.user, group=group, role='admin').first()
    if not user_membership:
        return JsonResponse({'success': False, 'error': '你沒有權限執行此操作'})
    
    if request.method == 'POST':
        new_role = request.POST.get('role')
        if new_role in ['admin', 'moderator', 'member']:
            try:
                membership.role = new_role
                membership.save()
                
                # 創建通知
                Notification.objects.create(
                    recipient=membership.user,
                    sender=request.user,
                    notification_type='group_invite',
                    title='群組角色變更',
                    message=f'你在群組 {group.name} 的角色已變更為 {membership.get_role_display()}',
                    related_group=group
                )
                
                return JsonResponse({'success': True, 'message': '角色更新成功'})
            except Exception as e:
                import traceback
                print(f"Change role error: {str(e)}")
                print(traceback.format_exc())
                return JsonResponse({'success': False, 'error': f'操作失敗：{str(e)}'})
        else:
            return JsonResponse({'success': False, 'error': '無效的角色'})
    
    return JsonResponse({'success': False, 'error': '無效的請求方法'})

@login_required
def remove_member(request, membership_id):
    """移除群組成員"""
    membership = get_object_or_404(GroupMembership, id=membership_id)
    group = membership.group
    
    # 檢查權限：必須是管理員
    user_membership = GroupMembership.objects.filter(user=request.user, group=group, role='admin').first()
    if not user_membership:
        return JsonResponse({'success': False, 'error': '你沒有權限執行此操作'})
    
    # 不能移除自己
    if membership.user == request.user:
        return JsonResponse({'success': False, 'error': '不能移除自己'})
    
    if request.method == 'POST':
        try:
            removed_user = membership.user
            membership.delete()
            
            # 創建通知
            Notification.objects.create(
                recipient=removed_user,
                sender=request.user,
                notification_type='group_invite',
                title='已被移出群組',
                message=f'你已被移出群組 {group.name}',
                related_group=group
            )
            
            return JsonResponse({'success': True, 'message': '成員已移除'})
        except Exception as e:
            import traceback
            print(f"Remove member error: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({'success': False, 'error': f'操作失敗：{str(e)}'})
    
    return JsonResponse({'success': False, 'error': '無效的請求方法'})

@login_required
def chat_list(request):
    """聊天列表"""
    # 獲取用戶參與的所有聊天室
    chat_rooms = ChatRoom.objects.filter(
        participants=request.user,
        chatparticipant__is_active=True
    ).prefetch_related('participants', 'messages').distinct()
    
    # 為每個聊天室添加額外信息
    chat_data = []
    for room in chat_rooms:
        last_message = room.get_last_message()
        unread_count = room.get_unread_count(request.user)
        
        # 獲取聊天對象（私人聊天）
        other_user = None
        if room.room_type == 'private':
            participants = room.participants.exclude(id=request.user.id)
            other_user = participants.first() if participants.exists() else None
        
        chat_data.append({
            'room': room,
            'last_message': last_message,
            'unread_count': unread_count,
            'other_user': other_user,
        })
    
    context = {
        'chat_data': chat_data,
    }
    return render(request, 'social/chat_list.html', context)

@login_required
def chat_room(request, room_id):
    """聊天室詳情"""
    room = get_object_or_404(ChatRoom, id=room_id)
    
    # 檢查用戶是否有權限訪問此聊天室
    participant = ChatParticipant.objects.filter(user=request.user, chat_room=room).first()
    if not participant:
        messages.error(request, '你沒有權限訪問此聊天室。')
        return redirect('social:chat_list')
    
    # 如果參與者不活躍，重新激活
    if not participant.is_active:
        participant.is_active = True
        participant.save()
    
    # 獲取聊天消息
    chat_messages = ChatMessage.objects.filter(
        chat_room=room,
        is_deleted=False
    ).select_related('sender', 'reply_to').order_by('created_at')
    
    # 標記消息為已讀
    participant.last_read_at = timezone.now()
    participant.save()
    
    # 發送消息
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        message_type = request.POST.get('message_type', 'text')
        reply_to_id = request.POST.get('reply_to')
        
        if content or request.FILES.get('image') or request.FILES.get('file'):
            message = ChatMessage.objects.create(
                chat_room=room,
                sender=request.user,
                message_type=message_type,
                content=content
            )
            
            # 處理圖片上傳
            if request.FILES.get('image'):
                message.image = request.FILES['image']
                message.message_type = 'image'
            
            # 處理文件上傳
            if request.FILES.get('file'):
                message.file = request.FILES['file']
                message.message_type = 'file'
            
            # 處理回覆消息
            if reply_to_id:
                try:
                    reply_to = ChatMessage.objects.get(id=reply_to_id, chat_room=room)
                    message.reply_to = reply_to
                except ChatMessage.DoesNotExist:
                    pass
            
            message.save()
            
            # 更新聊天室的最後更新時間
            room.updated_at = timezone.now()
            room.save()
            
            # 如果是 AJAX 請求，返回 JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': {
                        'id': message.id,
                        'content': message.content,
                        'sender': message.sender.username,
                        'created_at': message.created_at.strftime('%H:%M'),
                        'message_type': message.message_type,
                    }
                })
            
            return redirect('social:chat_room', room_id=room_id)
    
    # 獲取其他參與者
    other_participants = room.participants.exclude(id=request.user.id)
    
    context = {
        'room': room,
        'messages': chat_messages,
        'other_participants': other_participants,
    }
    return render(request, 'social/chat_room.html', context)

@login_required
def start_private_chat(request, user_id):
    """開始私人聊天"""
    other_user = get_object_or_404(User, id=user_id)
    
    if other_user == request.user:
        messages.error(request, '不能與自己聊天。')
        return redirect('social:chat_list')
    
    # 檢查是否已存在私人聊天室
    existing_room = ChatRoom.objects.filter(
        room_type='private',
        participants=request.user
    ).filter(participants=other_user).first()
    
    if existing_room:
        return redirect('social:chat_room', room_id=existing_room.id)
    
    # 創建新的私人聊天室
    room = ChatRoom.objects.create(
        room_type='private',
        created_by=request.user
    )
    
    # 添加參與者
    ChatParticipant.objects.create(user=request.user, chat_room=room, is_active=True)
    ChatParticipant.objects.create(user=other_user, chat_room=room, is_active=True)
    
    # 不創建系統消息，直接跳轉
    return redirect('social:chat_room', room_id=room.id)

@login_required
def create_group_chat(request):
    """創建群組聊天"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        participant_ids = request.POST.getlist('participants')
        
        if not name:
            messages.error(request, '請輸入群組聊天名稱。')
            return redirect('social:chat_list')
        
        if len(participant_ids) < 1:
            messages.error(request, '請至少選擇一個參與者。')
            return redirect('social:chat_list')
        
        # 創建群組聊天室
        room = ChatRoom.objects.create(
            name=name,
            room_type='group',
            created_by=request.user
        )
        
        # 添加創建者
        ChatParticipant.objects.create(user=request.user, chat_room=room, is_active=True)
        
        # 添加其他參與者
        for user_id in participant_ids:
            try:
                user = User.objects.get(id=user_id)
                ChatParticipant.objects.create(user=user, chat_room=room, is_active=True)
            except User.DoesNotExist:
                continue
        
        # 不創建系統消息
        messages.success(request, '群組聊天創建成功！')
        return redirect('social:chat_room', room_id=room.id)
    
    # 獲取好友列表
    friends = Friendship.objects.filter(
        Q(from_user=request.user, status='accepted') |
        Q(to_user=request.user, status='accepted')
    ).select_related('from_user', 'to_user')
    
    friend_users = []
    for friendship in friends:
        friend_user = friendship.to_user if friendship.from_user == request.user else friendship.from_user
        friend_users.append(friend_user)
    
    context = {
        'friends': friend_users,
    }
    return render(request, 'social/create_group_chat.html', context)

@login_required
def delete_message(request, message_id):
    """刪除消息"""
    if request.method == 'POST':
        message = get_object_or_404(ChatMessage, id=message_id, sender=request.user)
        message.is_deleted = True
        message.content = '此消息已被刪除'
        message.save()
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': '無效的請求方法'})

@login_required
def leave_chat_room(request, room_id):
    """離開聊天室"""
    room = get_object_or_404(ChatRoom, id=room_id)
    participant = get_object_or_404(ChatParticipant, user=request.user, chat_room=room)
    
    if request.method == 'POST':
        participant.is_active = False
        participant.save()
        
        # 不創建系統消息
        messages.success(request, '已離開聊天室。')
        return redirect('social:chat_list')
    
    return JsonResponse({'success': False, 'error': '無效的請求方法'})

@login_required
def like_post(request, post_id):
    """按讚動態"""
    post = get_object_or_404(SocialPost, id=post_id)
    like, created = PostLike.objects.get_or_create(user=request.user, post=post)
    
    if not created:
        like.delete()
        action = 'unliked'
    else:
        action = 'liked'
        # 更新被按讚用戶的統計
        post.user.social_profile.update_statistics()
    
    # 更新當前用戶的統計
    request.user.social_profile.update_statistics()
    
    return JsonResponse({
        'status': 'success',
        'action': action,
        'likes_count': post.likes.count(),
        'user_likes_received': request.user.social_profile.total_likes_received
    })

@login_required
def accept_friend_request(request, request_id):
    """接受好友請求"""
    friend_request = get_object_or_404(Friendship, id=request_id, to_user=request.user, status='pending')
    friend_request.status = 'accepted'
    friend_request.save()
    
    # 更新雙方的統計數據
    request.user.social_profile.update_statistics()
    friend_request.from_user.social_profile.update_statistics()
    
    messages.success(request, f'已接受 {friend_request.from_user.username} 的好友請求！')
    return redirect('social:friends')

@login_required
def post_detail(request, post_id):
    post = get_object_or_404(SocialPost, id=post_id)
    return render(request, 'social/post_detail.html', {'post': post}) 