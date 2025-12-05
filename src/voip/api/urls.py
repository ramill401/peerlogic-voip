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
    
    # Call Control
    path('connections/<str:connection_id>/calls/', views.list_active_calls, name='list-active-calls'),
    path('connections/<str:connection_id>/calls/<str:call_id>/', views.get_call, name='get-call'),
    path('connections/<str:connection_id>/calls/<str:call_id>/transfer/', views.transfer_call, name='transfer-call'),
    path('connections/<str:connection_id>/calls/<str:call_id>/hold/', views.hold_call, name='hold-call'),
    path('connections/<str:connection_id>/calls/<str:call_id>/resume/', views.resume_call, name='resume-call'),
    path('connections/<str:connection_id>/calls/<str:call_id>/mute/', views.mute_call, name='mute-call'),
    path('connections/<str:connection_id>/calls/<str:call_id>/unmute/', views.unmute_call, name='unmute-call'),
    path('connections/<str:connection_id>/calls/<str:call_id>/hangup/', views.hangup_call, name='hangup-call'),
    path('connections/<str:connection_id>/calls/<str:call_id>/recording/start/', views.start_recording, name='start-recording'),
    path('connections/<str:connection_id>/calls/<str:call_id>/recording/stop/', views.stop_recording, name='stop-recording'),
    path('connections/<str:connection_id>/calls/<str:call_id>/park/', views.park_call, name='park-call'),
    path('connections/<str:connection_id>/calls/unpark/', views.unpark_call, name='unpark-call'),
    
    # Conference
    path('connections/<str:connection_id>/conferences/', views.create_conference, name='create-conference'),
    path('connections/<str:connection_id>/conferences/<str:conference_id>/add/', views.add_to_conference, name='add-to-conference'),
    path('connections/<str:connection_id>/conferences/<str:conference_id>/remove/<str:call_id>/', views.remove_from_conference, name='remove-from-conference'),
]

