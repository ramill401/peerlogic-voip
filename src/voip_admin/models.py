"""
Core models for Peerlogic VoIP Admin.

These models store:
- VoIP provider configurations (NetSapiens, RingCentral, etc.)
- Practice/organization connections to providers
- Encrypted credentials
- Audit logs
"""

import uuid
from django.db import models
from django.contrib.auth.models import User


class VoIPProvider(models.Model):
    """
    Represents a VoIP provider type (NetSapiens, RingCentral, etc.)
    This is like a "template" - each provider has different capabilities.
    """
    
    PROVIDER_CHOICES = [
        ('netsapiens', 'NetSapiens'),
        ('ringcentral', 'RingCentral'),
        ('8x8', '8x8'),
        ('vonage', 'Vonage'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    provider_type = models.CharField(max_length=50, choices=PROVIDER_CHOICES)
    description = models.TextField(blank=True)
    
    # Provider capabilities (what can this provider do?)
    supports_users = models.BooleanField(default=True)
    supports_devices = models.BooleanField(default=True)
    supports_call_queues = models.BooleanField(default=False)
    supports_auto_attendant = models.BooleanField(default=False)
    supports_call_recording = models.BooleanField(default=False)
    supports_voicemail = models.BooleanField(default=True)
    supports_sms = models.BooleanField(default=False)
    
    # API configuration template
    api_base_url_template = models.URLField(
        blank=True,
        help_text="Template URL, e.g., https://{domain}.netsapiens.com/ns-api/"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'voip_provider'
        verbose_name = 'VoIP Provider'
        verbose_name_plural = 'VoIP Providers'
    
    def __str__(self):
        return f"{self.name} ({self.provider_type})"


class Practice(models.Model):
    """
    Represents a dental/medical practice (Peerlogic customer).
    This is the multi-tenant boundary - each practice has its own VoIP config.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    external_id = models.CharField(
        max_length=100, 
        unique=True,
        help_text="ID from main Peerlogic system"
    )
    
    # Contact info
    primary_email = models.EmailField(blank=True)
    primary_phone = models.CharField(max_length=20, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'voip_practice'
        verbose_name = 'Practice'
        verbose_name_plural = 'Practices'
    
    def __str__(self):
        return self.name


class ProviderConnection(models.Model):
    """
    Links a Practice to a VoIP Provider with credentials.
    A practice might have multiple connections (e.g., main office + branch).
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending Setup'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Connection Error'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    practice = models.ForeignKey(
        Practice, 
        on_delete=models.CASCADE,
        related_name='provider_connections'
    )
    provider = models.ForeignKey(
        VoIPProvider,
        on_delete=models.PROTECT,
        related_name='connections'
    )
    
    # Connection name (e.g., "Main Office", "Downtown Branch")
    name = models.CharField(max_length=100)
    
    # Provider-specific configuration
    # For NetSapiens: domain, reseller, etc.
    config = models.JSONField(
        default=dict,
        help_text="Provider-specific configuration (domain, territory, etc.)"
    )
    
    # Encrypted credentials stored separately for security
    # We'll create a separate model for this
    
    # Connection status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    last_sync_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_connections'
    )
    
    class Meta:
        db_table = 'voip_provider_connection'
        verbose_name = 'Provider Connection'
        verbose_name_plural = 'Provider Connections'
        unique_together = ['practice', 'name']
    
    def __str__(self):
        return f"{self.practice.name} - {self.name} ({self.provider.name})"


class ProviderCredential(models.Model):
    """
    Stores encrypted credentials for a provider connection.
    Separated from ProviderConnection for security.
    """
    
    CREDENTIAL_TYPE_CHOICES = [
        ('oauth', 'OAuth 2.0'),
        ('api_key', 'API Key'),
        ('basic', 'Basic Auth (Username/Password)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    connection = models.OneToOneField(
        ProviderConnection,
        on_delete=models.CASCADE,
        related_name='credentials'
    )
    
    credential_type = models.CharField(max_length=20, choices=CREDENTIAL_TYPE_CHOICES)
    
    # Encrypted credential data
    # In production, this would be encrypted using the ENCRYPTION_KEY
    encrypted_data = models.BinaryField(
        help_text="Encrypted JSON containing credentials"
    )
    
    # For OAuth
    access_token_expires_at = models.DateTimeField(null=True, blank=True)
    refresh_token_expires_at = models.DateTimeField(null=True, blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'voip_provider_credential'
        verbose_name = 'Provider Credential'
        verbose_name_plural = 'Provider Credentials'
    
    def __str__(self):
        return f"Credentials for {self.connection}"


class AuditLog(models.Model):
    """
    Tracks all VoIP admin actions for compliance and debugging.
    """
    
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('read', 'Read'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('sync', 'Sync'),
        ('api_call', 'API Call'),
    ]
    
    RESULT_CHOICES = [
        ('success', 'Success'),
        ('failure', 'Failure'),
        ('partial', 'Partial Success'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # What happened
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    resource_type = models.CharField(max_length=50)  # e.g., 'user', 'device'
    resource_id = models.CharField(max_length=100, blank=True)
    
    # Context
    practice = models.ForeignKey(
        Practice,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'
    )
    connection = models.ForeignKey(
        ProviderConnection,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='voip_audit_logs'
    )
    
    # Details
    request_data = models.JSONField(default=dict, blank=True)
    response_data = models.JSONField(default=dict, blank=True)
    result = models.CharField(max_length=20, choices=RESULT_CHOICES)
    error_message = models.TextField(blank=True)
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    duration_ms = models.IntegerField(null=True, help_text="Request duration in milliseconds")
    
    class Meta:
        db_table = 'voip_audit_log'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['practice', '-created_at']),
            models.Index(fields=['action', '-created_at']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]
    
    def __str__(self):
        return f"{self.action} {self.resource_type} - {self.result} - {self.created_at}"


class IDMapping(models.Model):
    """
    Maps Peerlogic resource IDs to provider-specific IDs.
    
    This ensures we don't leak provider IDs into the UI and allows us to
    maintain stable Peerlogic IDs even if provider IDs change.
    """
    
    RESOURCE_TYPE_CHOICES = [
        ('user', 'User'),
        ('device', 'Device'),
        ('call_queue', 'Call Queue'),
        ('number', 'Phone Number'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Connection context
    connection = models.ForeignKey(
        ProviderConnection,
        on_delete=models.CASCADE,
        related_name='id_mappings'
    )
    
    # Resource identification
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPE_CHOICES)
    peerlogic_id = models.CharField(
        max_length=100,
        help_text="Stable ID used in Peerlogic API/UI"
    )
    provider_id = models.CharField(
        max_length=100,
        help_text="Provider-specific ID (e.g., NetSapiens user_id)"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'voip_id_mapping'
        verbose_name = 'ID Mapping'
        verbose_name_plural = 'ID Mappings'
        unique_together = ['connection', 'resource_type', 'peerlogic_id']
        indexes = [
            models.Index(fields=['connection', 'resource_type', 'provider_id']),
            models.Index(fields=['connection', 'resource_type', 'peerlogic_id']),
        ]
    
    def __str__(self):
        return f"{self.resource_type}: {self.peerlogic_id} ↔ {self.provider_id}"
