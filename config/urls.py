"""
URL configuration for autovacuum project.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('authentication.urls')),
    path('history/', include('history.urls')),
    path('', include('connections.urls')),
    path('', include('scan.urls')),
]
