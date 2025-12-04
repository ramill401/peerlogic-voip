"""
Django Admin configuration for VoIP models.
"""

from django.contrib import admin
from .models import (
    VoIPProvider, 
    Practice, 
    ProviderConnection, 
    ProviderCredential,
    AuditLog
)


@admin.register(VoIPProvider)
class VoIPProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider_type', 'is_active', 'created_at']
    list_filter = ['provider_type', 'is_active']
    search_fields = ['name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Practice)
class PracticeAdmin(admin.ModelAdmin):
    list_display = ['name', 'external_id', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'external_id']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(ProviderConnection)
class ProviderConnectionAdmin(admin.ModelAdmin):
    list_display = ['practice', 'name', 'provider', 'status', 'last_sync_at']
    list_filter = ['status', 'provider']
    search_fields = ['practice__name', 'name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['practice', 'provider', 'created_by']


@admin.register(ProviderCredential)
class ProviderCredentialAdmin(admin.ModelAdmin):
    list_display = ['connection', 'credential_type', 'updated_at']
    list_filter = ['credential_type']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    # Hide the actual encrypted data in admin for security
    exclude = ['encrypted_data']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'action', 'resource_type', 'practice', 'user', 'result']
    list_filter = ['action', 'result', 'resource_type']
    search_fields = ['resource_id', 'practice__name']
    readonly_fields = [
        'id', 'action', 'resource_type', 'resource_id', 
        'practice', 'connection', 'user',
        'request_data', 'response_data', 'result', 
        'error_message', 'created_at', 'duration_ms'
    ]
    date_hierarchy = 'created_at'
    
    def has_add_permission(self, request):
        return False  # Audit logs should only be created by the system
    
    def has_change_permission(self, request, obj=None):
        return False  # Audit logs should never be modified
