from django.urls import path
from . import views

app_name = 'connections'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('api/connections/', views.add_connection, name='add_connection'),
    path('api/connections/test/', views.test_connection, name='test_connection'),
    path('api/connections/<int:connection_id>/test/', views.test_saved_connection, name='test_saved_connection'),
    path('api/connections/<int:connection_id>/update/', views.update_connection, name='update_connection'),
    path('api/connections/<int:connection_id>/delete/', views.delete_connection, name='delete_connection'),
]
