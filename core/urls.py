"""
URL configuration for core project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from .media_views import serve_media

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('courses.urls', namespace='courses')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('accounts/social/', include('allauth.urls')),
]

# Serve media files and visual debug toolbar during development only (DEBUG = True)
if settings.DEBUG:
    try:
        import debug_toolbar
        urlpatterns += [
            path('__debug__/', include(debug_toolbar.urls)),
        ]
    except ImportError:
        pass

    urlpatterns += [
        path('media/<path:media_path>', serve_media, name='serve_media'),
    ]
