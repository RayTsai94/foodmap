"""
URL configuration for ncufoodmap_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('restaurants.urls')),
    path('food_analysis/', include('food_analysis.urls')),
    path('accounts/', include('allauth.urls')),
    path('auth/', include('googleOauth.urls')),
    path('checkin/', include('checkin.urls')),
    path('article/', include('article.urls')),
    path('ai_recommendation/', include('ai_recommendation.urls')),
    path('ai_assistant/', include('ai_assistant.urls')),
    path('social/', include('social.urls')),
]

# 添加媒體文件的 URL 模式
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
        'show_indexes': True,
    }),
]

# 添加靜態文件的 URL 模式
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
