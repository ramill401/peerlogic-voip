"""
VoIP Service Layer.

Handles business logic between the REST API and provider adapters.
"""

import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime

from asgiref.sync import sync_to_async

from src.voip_admin.models import (
    Practice,
    ProviderConnection,
    ProviderCredential,
    AuditLog,
)
from src.voip.adapters import AdapterRegistry, AdapterConfig, AdapterResult
from src.voip.models import VoIPUserCreate, VoIPUserUpdate, VoIPDeviceCreate


logger = logging.getLogger("voip.services")


class VoIPServiceError(Exception):
    """Custom exception for VoIP service errors."""
    
    def __init__(self, code: str, message: str, details: Dict = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


class VoIPService:
    """
    Main service for VoIP operations.
    
    Usage:
        service = VoIPService(connection_id, user)
        await service.connect()
        users = await service.list_users()
        await service.disconnect()
    """
    
    def __init__(
        self, 
        connection_id: str,
        user=None,
    ):
        self.connection_id = connection_id
        self.user = user
        self._connection: Optional[ProviderConnection] = None
        self._adapter = None
        self._connected = False
    
    # ================================================================
    # CONNECTION MANAGEMENT
    # ================================================================
    
    def _load_connection(self) -> ProviderConnection:
        """Load the provider connection from database (sync)."""
        try:
            connection = ProviderConnection.objects.select_related(
                'provider', 'practice'
            ).get(id=self.connection_id)
            return connection
        except ProviderConnection.DoesNotExist:
            raise VoIPServiceError(
                code="CONNECTION_NOT_FOUND",
                message=f"Provider connection not found: {self.connection_id}"
            )
    
    def _load_credentials(self, connection: ProviderConnection) -> ProviderCredential:
        """Load credentials for a connection (sync)."""
        try:
            return ProviderCredential.objects.get(connection=connection)
        except ProviderCredential.DoesNotExist:
            raise VoIPServiceError(
                code="NO_CREDENTIALS",
                message="No credentials configured for this connection"
            )
    
    def _decrypt_credentials(self, credential: ProviderCredential) -> Dict[str, Any]:
        """Decrypt stored credentials."""
        try:
            raw_data = credential.encrypted_data
            
            if isinstance(raw_data, bytes):
                return json.loads(raw_data.decode('utf-8'))
            elif isinstance(raw_data, memoryview):
                return json.loads(bytes(raw_data).decode('utf-8'))
            else:
                return json.loads(str(raw_data))
        except Exception as e:
            logger.error(f"Failed to decrypt credentials: {e}")
            raise VoIPServiceError(
                code="CREDENTIAL_ERROR",
                message="Failed to decrypt credentials"
            )
    
    async def connect(self) -> None:
        """Initialize and connect the adapter."""
        # Load connection from database (sync operations wrapped in async)
        self._connection = await sync_to_async(self._load_connection)()
        
        if self._connection.status == 'inactive':
            raise VoIPServiceError(
                code="CONNECTION_INACTIVE",
                message="Provider connection is inactive"
            )
        
        # Get and decrypt credentials
        credential = await sync_to_async(self._load_credentials)(self._connection)
        decrypted_creds = self._decrypt_credentials(credential)
        
        # Build adapter config
        provider = self._connection.provider
        domain = self._connection.config.get('domain', '')
        base_url = provider.api_base_url_template.format(domain=domain)
        
        config = AdapterConfig(
            base_url=base_url,
            credentials=decrypted_creds,
            config=self._connection.config,
        )
        
        # Get adapter from registry
        self._adapter = AdapterRegistry.get_adapter(
            provider.provider_type,
            config
        )
        
        # Connect
        result = await self._adapter.connect()
        if not result.success:
            self._connection.status = 'error'
            self._connection.last_error = result.error.message
            await sync_to_async(self._connection.save)()
            raise VoIPServiceError(
                code=result.error.code,
                message=result.error.message
            )
        
        self._connected = True
        logger.info(f"Connected to {provider.name} for {self._connection.practice.name}")
    
    async def disconnect(self) -> None:
        """Disconnect the adapter."""
        if self._adapter:
            await self._adapter.disconnect()
            self._connected = False
    
    def _ensure_connected(self):
        """Raise error if not connected."""
        if not self._connected:
            raise VoIPServiceError(
                code="NOT_CONNECTED",
                message="Service not connected. Call connect() first."
            )
    
    # ================================================================
    # AUDIT LOGGING
    # ================================================================
    
    async def _log_action(
        self,
        action: str,
        resource_type: str,
        resource_id: str = "",
        request_data: Dict = None,
        response_data: Dict = None,
        result: str = "success",
        error_message: str = "",
        duration_ms: int = None,
    ) -> None:
        """Create an audit log entry."""
        @sync_to_async
        def _create_log():
            try:
                return AuditLog.objects.create(
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    practice=self._connection.practice if self._connection else None,
                    connection=self._connection,
                    user=self.user if self.user and hasattr(self.user, 'id') else None,
                    request_data=request_data or {},
                    response_data=response_data or {},
                    result=result,
                    error_message=error_message,
                    duration_ms=duration_ms,
                )
            except Exception as e:
                logger.error(f"Failed to create audit log: {e}")
        
        await _create_log()
    
    # ================================================================
    # USER OPERATIONS
    # ================================================================
    
    async def list_users(
        self,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
    ) -> Dict:
        """List all users for this connection."""
        self._ensure_connected()
        
        start_time = datetime.now()
        result = await self._adapter.list_users(
            page=page,
            page_size=page_size,
            search=search,
        )
        duration = int((datetime.now() - start_time).total_seconds() * 1000)
        
        if result.success:
            # Convert Pydantic model to dict
            data = result.data.model_dump()
            
            await self._log_action(
                action="read",
                resource_type="user",
                request_data={"page": page, "page_size": page_size, "search": search},
                response_data={"total": data.get("total", 0)},
                result="success",
                duration_ms=duration,
            )
            return data
        else:
            await self._log_action(
                action="read",
                resource_type="user",
                result="failure",
                error_message=result.error.message,
                duration_ms=duration,
            )
            raise VoIPServiceError(
                code=result.error.code,
                message=result.error.message
            )
    
    async def get_user(self, user_id: str) -> Dict:
        """Get a single user by ID."""
        self._ensure_connected()
        
        start_time = datetime.now()
        result = await self._adapter.get_user(user_id)
        duration = int((datetime.now() - start_time).total_seconds() * 1000)
        
        if result.success:
            data = result.data.model_dump()
            
            await self._log_action(
                action="read",
                resource_type="user",
                resource_id=user_id,
                result="success",
                duration_ms=duration,
            )
            return data
        else:
            await self._log_action(
                action="read",
                resource_type="user",
                resource_id=user_id,
                result="failure",
                error_message=result.error.message,
                duration_ms=duration,
            )
            raise VoIPServiceError(
                code=result.error.code,
                message=result.error.message
            )
    
    async def create_user(self, user_data: Dict) -> Dict:
        """Create a new user."""
        self._ensure_connected()
        
        start_time = datetime.now()
        create_data = VoIPUserCreate(**user_data)
        result = await self._adapter.create_user(create_data)
        duration = int((datetime.now() - start_time).total_seconds() * 1000)
        
        if result.success:
            data = result.data.model_dump()
            
            await self._log_action(
                action="create",
                resource_type="user",
                resource_id=data.get("id", ""),
                request_data=user_data,
                result="success",
                duration_ms=duration,
            )
            return data
        else:
            await self._log_action(
                action="create",
                resource_type="user",
                request_data=user_data,
                result="failure",
                error_message=result.error.message,
                duration_ms=duration,
            )
            raise VoIPServiceError(
                code=result.error.code,
                message=result.error.message
            )
    
    async def update_user(self, user_id: str, user_data: Dict) -> Dict:
        """Update a user."""
        self._ensure_connected()
        
        start_time = datetime.now()
        update_data = VoIPUserUpdate(**user_data)
        result = await self._adapter.update_user(user_id, update_data)
        duration = int((datetime.now() - start_time).total_seconds() * 1000)
        
        if result.success:
            data = result.data.model_dump()
            
            await self._log_action(
                action="update",
                resource_type="user",
                resource_id=user_id,
                request_data=user_data,
                result="success",
                duration_ms=duration,
            )
            return data
        else:
            await self._log_action(
                action="update",
                resource_type="user",
                resource_id=user_id,
                request_data=user_data,
                result="failure",
                error_message=result.error.message,
                duration_ms=duration,
            )
            raise VoIPServiceError(
                code=result.error.code,
                message=result.error.message
            )
    
    async def delete_user(self, user_id: str) -> Dict:
        """Delete a user."""
        self._ensure_connected()
        
        start_time = datetime.now()
        result = await self._adapter.delete_user(user_id)
        duration = int((datetime.now() - start_time).total_seconds() * 1000)
        
        if result.success:
            await self._log_action(
                action="delete",
                resource_type="user",
                resource_id=user_id,
                result="success",
                duration_ms=duration,
            )
            return {"deleted": True, "user_id": user_id}
        else:
            await self._log_action(
                action="delete",
                resource_type="user",
                resource_id=user_id,
                result="failure",
                error_message=result.error.message,
                duration_ms=duration,
            )
            raise VoIPServiceError(
                code=result.error.code,
                message=result.error.message
            )
    
    # ================================================================
    # DEVICE OPERATIONS
    # ================================================================
    
    async def list_devices(
        self,
        page: int = 1,
        page_size: int = 50,
        user_id: Optional[str] = None,
    ) -> Dict:
        """List all devices for this connection."""
        self._ensure_connected()
        
        start_time = datetime.now()
        result = await self._adapter.list_devices(
            page=page,
            page_size=page_size,
            user_id=user_id,
        )
        duration = int((datetime.now() - start_time).total_seconds() * 1000)
        
        if result.success:
            data = result.data.model_dump()
            
            await self._log_action(
                action="read",
                resource_type="device",
                request_data={"page": page, "user_id": user_id},
                response_data={"total": data.get("total", 0)},
                result="success",
                duration_ms=duration,
            )
            return data
        else:
            await self._log_action(
                action="read",
                resource_type="device",
                result="failure",
                error_message=result.error.message,
                duration_ms=duration,
            )
            raise VoIPServiceError(
                code=result.error.code,
                message=result.error.message
            )
    
    async def get_device(self, device_id: str) -> Dict:
        """Get a single device."""
        self._ensure_connected()
        
        result = await self._adapter.get_device(device_id)
        
        if result.success:
            return result.data.model_dump()
        else:
            raise VoIPServiceError(
                code=result.error.code,
                message=result.error.message
            )
    
    async def create_device(self, device_data: Dict) -> Dict:
        """Create a new device."""
        self._ensure_connected()
        
        create_data = VoIPDeviceCreate(**device_data)
        result = await self._adapter.create_device(create_data)
        
        if result.success:
            data = result.data.model_dump()
            
            await self._log_action(
                action="create",
                resource_type="device",
                resource_id=data.get("id", ""),
                request_data=device_data,
                result="success",
            )
            return data
        else:
            raise VoIPServiceError(
                code=result.error.code,
                message=result.error.message
            )
    
    async def delete_device(self, device_id: str) -> Dict:
        """Delete a device."""
        self._ensure_connected()
        
        result = await self._adapter.delete_device(device_id)
        
        if result.success:
            await self._log_action(
                action="delete",
                resource_type="device",
                resource_id=device_id,
                result="success",
            )
            return {"deleted": True, "device_id": device_id}
        else:
            raise VoIPServiceError(
                code=result.error.code,
                message=result.error.message
            )
