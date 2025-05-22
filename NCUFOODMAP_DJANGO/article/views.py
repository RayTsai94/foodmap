from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from .models import Article, Comment
from restaurants.models import Restaurant
from django.contrib.auth.models import User

# Create your views here.

def home(request):
    # 獲取最新文章
    articles = Article.objects.all()[:5]
    
    # 獲取熱門文章（根據評論數量排序）
    popular_articles = Article.objects.annotate(
        comment_count=Count('comments')
    ).order_by('-comment_count')[:5]
    
    # 獲取網站統計數據
    context = {
        'articles': articles,
        'popular_articles': popular_articles,
        'total_articles': Article.objects.count(),
        'total_comments': Comment.objects.count(),
        'total_users': User.objects.count(),
        'total_restaurants': Restaurant.objects.count(),
    }
    
    return render(request, 'article/articlehome.html', context)

def article_list(request):
    articles = Article.objects.all()
    return render(request, 'article/article_list.html', {'articles': articles})

def article_detail(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    # 獲取相關文章（同一作者的其他文章）
    related_articles = Article.objects.filter(author=article.author).exclude(id=article.id)[:5]
    return render(request, 'article/article_detail.html', {
        'article': article,
        'related_articles': related_articles
    })

@login_required
def article_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        if title and content:
            article = Article.objects.create(
                title=title,
                content=content,
                author=request.user
            )
            messages.success(request, '文章發布成功！')
            return redirect('article_detail', article_id=article.id)
        else:
            messages.error(request, '請填寫標題和內容！')
    return render(request, 'article/article_form.html')

@login_required
def article_edit(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    if article.author != request.user:
        messages.error(request, '您沒有權限編輯此文章！')
        return redirect('article_detail', article_id=article.id)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        if title and content:
            article.title = title
            article.content = content
            article.save()
            messages.success(request, '文章更新成功！')
            return redirect('article_detail', article_id=article.id)
        else:
            messages.error(request, '請填寫標題和內容！')
    
    return render(request, 'article/article_form.html', {'article': article})

@login_required
def article_delete(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    if article.author != request.user:
        messages.error(request, '您沒有權限刪除此文章！')
        return redirect('article_detail', article_id=article.id)
    
    if request.method == 'POST':
        article.delete()
        messages.success(request, '文章已刪除！')
        return redirect('article_list')
    
    return render(request, 'article/article_confirm_delete.html', {'article': article})

@login_required
def article_comment(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Comment.objects.create(
                article=article,
                author=request.user,
                content=content
            )
            messages.success(request, '評論發布成功！')
        else:
            messages.error(request, '請填寫評論內容！')
    return redirect('article_detail', article_id=article.id)

@login_required
def article_comment_delete(request, article_id, comment_id):
    article = get_object_or_404(Article, id=article_id)
    comment = get_object_or_404(Comment, id=comment_id, article=article)
    if comment.author != request.user:
        messages.error(request, '您沒有權限刪除此評論！')
    else:
        comment.delete()
        messages.success(request, '評論已刪除！')
    return redirect('article_detail', article_id=article.id)
