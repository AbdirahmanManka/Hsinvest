from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
import os

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),  # Homepage and main pages
    path('blog/', include('blog.urls')),  # Blog functionality
    path('users/', include('users.urls')),  # Authentication (includes logout)
    path('newsletter/', include('newsletter.urls')),  # Newsletter
    path('analytics/', include('analytics.urls')),  # Analytics (optional)
    path('ckeditor/', include('ckeditor_uploader.urls')),  # CKEditor uploads
]

# Serve media files (both development and local production testing)
# Debug: Print media configuration
print(f"🖼️  MEDIA_URL: {settings.MEDIA_URL}")
print(f"📁 MEDIA_ROOT: {settings.MEDIA_ROOT}")
print(f"📁 MEDIA_ROOT exists: {os.path.exists(str(settings.MEDIA_ROOT))}")

# Add media URL pattern manually
urlpatterns += [
    path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}, name='media'),
]

print(f"✅ Media files will be served from: {settings.MEDIA_URL}")

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)