from django.urls import path
from . import views

app_name = 'scan'

urlpatterns = [
    path('api/connections/<int:connection_id>/bloat/', views.check_bloat, name='check_bloat'),
    path('api/connections/<int:connection_id>/vacuum/', views.run_vacuum, name='run_vacuum'),
]
