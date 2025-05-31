from django import forms
from django.contrib.auth.models import User
from .models import SocialPost, PostComment, FoodGroup, GroupChallenge, UserProfile

class SocialPostForm(forms.ModelForm):
    """社交動態發布表單"""
    class Meta:
        model = SocialPost
        fields = ['post_type', 'content', 'image', 'is_public']
        widgets = {
            'post_type': forms.Select(attrs={
                'class': 'form-control',
                'id': 'post_type'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '分享你的想法...'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'post_type': '動態類型',
            'content': '內容',
            'image': '圖片',
            'is_public': '公開分享'
        }

class PostCommentForm(forms.ModelForm):
    """動態評論表單"""
    class Meta:
        model = PostComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': '寫下你的評論...'
            })
        }
        labels = {
            'content': '評論內容'
        }

class FoodGroupForm(forms.ModelForm):
    """飲食群組創建表單"""
    class Meta:
        model = FoodGroup
        fields = ['name', 'description', 'image', 'is_public']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '群組名稱'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '群組描述'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'name': '群組名稱',
            'description': '群組描述',
            'image': '群組圖片',
            'is_public': '公開群組'
        }

class GroupChallengeForm(forms.ModelForm):
    """群組挑戰創建表單"""
    class Meta:
        model = GroupChallenge
        fields = ['title', 'description', 'challenge_type', 'target_value', 'start_date', 'end_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '挑戰標題'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '挑戰描述'
            }),
            'challenge_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'target_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            })
        }
        labels = {
            'title': '挑戰標題',
            'description': '挑戰描述',
            'challenge_type': '挑戰類型',
            'target_value': '目標值',
            'start_date': '開始日期',
            'end_date': '結束日期'
        }

class UserProfileForm(forms.ModelForm):
    """用戶資料編輯表單"""
    class Meta:
        model = UserProfile
        fields = ['bio', 'avatar', 'location', 'birth_date', 'show_email', 'show_location', 'show_birth_date']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '介紹一下自己...'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '所在地'
            }),
            'birth_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'show_email': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'show_location': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'show_birth_date': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'bio': '個人簡介',
            'avatar': '頭像',
            'location': '所在地',
            'birth_date': '生日',
            'show_email': '顯示電子郵件',
            'show_location': '顯示所在地',
            'show_birth_date': '顯示生日'
        }

class FriendSearchForm(forms.Form):
    """好友搜尋表單"""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '輸入用戶名搜尋好友...'
        }),
        label='搜尋用戶'
    ) 