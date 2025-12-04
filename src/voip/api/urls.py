"""
URL routing for VoIP API.
"""

from django.urls import path
from . import views
from . import setup_views

urlpatterns = [
    # Health & Info
    path('health/', views.api_health, name='api-health'),
    path('info/', views.api_info, name='api-info'),
    # Setup (one-time)
    path('setup/', setup_views.run_initial_setup, name='api-setup'),
    
    # Connections
    path('connections/', views.list_connections, name='list-connections'),
    path('connections/<str:connection_id>/', views.get_connection, name='get-connection'),
    path('connections/<str:connection_id>/test/', views.test_connection, name='test-connection'),
    
    # Users
    path('connections/<str:connection_id>/users/', views.list_users, name='list-users'),
    path('connections/<str:connection_id>/users/create/', views.create_user, name='create-user'),
    path('connections/<str:connection_id>/users/<str:user_id>/', views.get_user, name='get-user'),
    path('connections/<str:connection_id>/users/<str:user_id>/update/', views.update_user, name='update-user'),
    path('connections/<str:connection_id>/users/<str:user_id>/delete/', views.delete_user, name='delete-user'),
    
    # Devices
    path('connections/<str:connection_id>/devices/', views.list_devices, name='list-devices'),
    path('connections/<str:connection_id>/devices/create/', views.create_device, name='create-device'),
    path('connections/<str:connection_id>/devices/<str:device_id>/', views.get_device, name='get-device'),
    path('connections/<str:connection_id>/devices/<str:device_id>/delete/', views.delete_device, name='delete-device'),
]

