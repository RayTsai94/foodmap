import os
import django

# 設定 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ncufoodmap_backend.settings')
django.setup()

from social.models import ChatMessage

# 清除所有系統消息
system_messages = ChatMessage.objects.filter(message_type='system')
count = system_messages.count()
system_messages.delete()

print(f"已刪除 {count} 條系統消息") 