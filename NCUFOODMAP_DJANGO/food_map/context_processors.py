from django.conf import settings

def google_maps_api_key(request):
    """
    將 Google Maps API 金鑰添加到所有模板的上下文中
    """
    return {
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY
    } 