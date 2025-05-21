from django.shortcuts import render, redirect
from django.contrib.auth import logout
from allauth.socialaccount.models import SocialApp, SocialAccount
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def home(request):
    """Google OAuth 登入頁面"""
    # 檢查是否已設置 Google 社交應用
    has_google_provider = SocialApp.objects.filter(provider='google').exists()
    
    context = {
        'has_google_provider': has_google_provider
    }
    
    # 如果用戶已登入，獲取其社交帳號信息
    if request.user.is_authenticated:
        try:
            social_account = SocialAccount.objects.get(user=request.user, provider='google')
            context['social_account'] = social_account
            context['extra_data'] = social_account.extra_data
        except SocialAccount.DoesNotExist:
            pass
    
    # 使用專屬於googleOauth的模板
    return render(request, 'auth/home.html', context)

@login_required
def logout_view(request):
    """登出功能"""
    logout(request)
    messages.success(request, "您已成功登出")
    return redirect('/')



