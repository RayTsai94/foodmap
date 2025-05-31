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
    UserProfile, Notification
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
            messages.success(request, '動態發布成功！')
            return redirect('social:feed')
    else:
        form = SocialPostForm()
    
    # 獲取用戶統計
    user_stats = {
        'posts_count': SocialPost.objects.filter(user=request.user).count(),
        'friends_count': len(friend_ids) - 1,  # 減去自己
        'likes_received': PostLike.objects.filter(post__user=request.user).count(),
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
    
    # 群組成員
    members = GroupMembership.objects.filter(group=group).select_related('user')
    
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
        'members': members,
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
            notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
            notification.is_read = True
            notification.save()
            return JsonResponse({'success': True})
    
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
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': '無效的請求方法'}) 