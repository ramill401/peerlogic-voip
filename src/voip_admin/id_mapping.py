"""
ID Mapping Service.

Maps Peerlogic resource IDs to provider-specific IDs and vice versa.
This ensures we don't leak provider IDs into the UI.
"""

import uuid
from typing import Optional
from asgiref.sync import sync_to_async

from src.voip_admin.models import ProviderConnection, IDMapping


class IDMappingService:
    """Service for managing ID mappings between Peerlogic and provider IDs."""
    
    @staticmethod
    @sync_to_async
    def get_or_create_peerlogic_id(
        connection: ProviderConnection,
        resource_type: str,
        provider_id: str
    ) -> str:
        """
        Get or create a Peerlogic ID for a provider resource.
        
        Args:
            connection: The provider connection
            resource_type: Type of resource ('user', 'device', etc.)
            provider_id: The provider's ID for this resource
        
        Returns:
            Peerlogic ID (stable UUID)
        """
        mapping, created = IDMapping.objects.get_or_create(
            connection=connection,
            resource_type=resource_type,
            provider_id=provider_id,
            defaults={'peerlogic_id': str(uuid.uuid4())}
        )
        return mapping.peerlogic_id
    
    @staticmethod
    @sync_to_async
    def get_provider_id(
        connection: ProviderConnection,
        resource_type: str,
        peerlogic_id: str
    ) -> Optional[str]:
        """
        Get provider ID from Peerlogic ID.
        
        Args:
            connection: The provider connection
            resource_type: Type of resource
            peerlogic_id: The Peerlogic ID
        
        Returns:
            Provider ID or None if not found
        """
        try:
            mapping = IDMapping.objects.get(
                connection=connection,
                resource_type=resource_type,
                peerlogic_id=peerlogic_id
            )
            return mapping.provider_id
        except IDMapping.DoesNotExist:
            return None
    
    @staticmethod
    @sync_to_async
    def get_peerlogic_id(
        connection: ProviderConnection,
        resource_type: str,
        provider_id: str
    ) -> Optional[str]:
        """
        Get Peerlogic ID from provider ID.
        
        Args:
            connection: The provider connection
            resource_type: Type of resource
            provider_id: The provider's ID
        
        Returns:
            Peerlogic ID or None if not found
        """
        try:
            mapping = IDMapping.objects.get(
                connection=connection,
                resource_type=resource_type,
                provider_id=provider_id
            )
            return mapping.peerlogic_id
        except IDMapping.DoesNotExist:
            return None
    
    @staticmethod
    @sync_to_async
    def delete_mapping(
        connection: ProviderConnection,
        resource_type: str,
        peerlogic_id: str
    ) -> bool:
        """
        Delete an ID mapping.
        
        Returns:
            True if deleted, False if not found
        """
        try:
            mapping = IDMapping.objects.get(
                connection=connection,
                resource_type=resource_type,
                peerlogic_id=peerlogic_id
            )
            mapping.delete()
            return True
        except IDMapping.DoesNotExist:
            return False

