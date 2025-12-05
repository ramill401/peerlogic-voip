"""
Base VoIP Adapter Interface.

All provider adapters (NetSapiens, RingCentral, etc.) must inherit from
this base class and implement all abstract methods.

This ensures every provider can be used interchangeably by Peerlogic.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

from src.voip.models.schemas import (
    VoIPUser, VoIPUserCreate, VoIPUserUpdate, VoIPUserList,
    VoIPDevice, VoIPDeviceCreate, VoIPDeviceList,
    VoIPCallQueue,
    VoIPCall, VoIPCallList,
    TransferCallRequest, ConferenceRequest, RecordingRequest,
    VoIPError,
)


@dataclass
class AdapterConfig:
    """Configuration passed to adapter on initialization."""
    
    # Connection details
    base_url: str
    
    # Authentication
    credentials: Dict[str, Any]  # Decrypted credentials
    
    # Provider-specific config
    config: Dict[str, Any]  # From ProviderConnection.config
    
    # Settings
    timeout: int = 30
    max_retries: int = 3


class AdapterResult:
    """
    Wrapper for adapter operation results.
    Contains either data or an error, never both.
    """
    
    def __init__(
        self, 
        success: bool,
        data: Any = None,
        error: Optional[VoIPError] = None
    ):
        self.success = success
        self.data = data
        self.error = error
    
    @classmethod
    def ok(cls, data: Any) -> "AdapterResult":
        """Create a successful result."""
        return cls(success=True, data=data)
    
    @classmethod
    def fail(cls, code: str, message: str, details: Dict = None) -> "AdapterResult":
        """Create a failed result."""
        return cls(
            success=False,
            error=VoIPError(code=code, message=message, details=details)
        )


class BaseVoIPAdapter(ABC):
    """
    Abstract base class for all VoIP provider adapters.
    
    Each provider (NetSapiens, RingCentral, etc.) implements this interface.
    This ensures consistent behavior across all providers.
    
    Usage:
        adapter = NetSapiensAdapter(config)
        result = await adapter.list_users()
        if result.success:
            users = result.data
        else:
            print(f"Error: {result.error.message}")
    """
    
    # Override in subclass
    PROVIDER_TYPE: str = "base"
    PROVIDER_NAME: str = "Base Provider"
    
    def __init__(self, config: AdapterConfig):
        self.config = config
        self._client = None  # HTTP client, initialized in connect()
    
    # ================================================================
    # CONNECTION MANAGEMENT
    # ================================================================
    
    @abstractmethod
    async def connect(self) -> AdapterResult:
        """
        Initialize connection to the provider.
        Should validate credentials and set up HTTP client.
        
        Returns:
            AdapterResult with connection status
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Clean up connections and resources."""
        pass
    
    @abstractmethod
    async def health_check(self) -> AdapterResult:
        """
        Check if the provider connection is healthy.
        
        Returns:
            AdapterResult with health status
        """
        pass
    
    # ================================================================
    # USER MANAGEMENT
    # ================================================================
    
    @abstractmethod
    async def list_users(
        self,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
        status: Optional[str] = None,
    ) -> AdapterResult:
        """
        List all users/extensions.
        
        Args:
            page: Page number (1-indexed)
            page_size: Number of results per page
            search: Optional search term (name, email, extension)
            status: Optional filter by status
        
        Returns:
            AdapterResult containing VoIPUserList
        """
        pass
    
    @abstractmethod
    async def get_user(self, user_id: str) -> AdapterResult:
        """
        Get a single user by ID.
        
        Args:
            user_id: The user's ID (adapter-specific)
        
        Returns:
            AdapterResult containing VoIPUser
        """
        pass
    
    @abstractmethod
    async def create_user(self, user_data: VoIPUserCreate) -> AdapterResult:
        """
        Create a new user.
        
        Args:
            user_data: User creation data
        
        Returns:
            AdapterResult containing created VoIPUser
        """
        pass
    
    @abstractmethod
    async def update_user(
        self, 
        user_id: str, 
        user_data: VoIPUserUpdate
    ) -> AdapterResult:
        """
        Update an existing user.
        
        Args:
            user_id: The user's ID
            user_data: Fields to update
        
        Returns:
            AdapterResult containing updated VoIPUser
        """
        pass
    
    @abstractmethod
    async def delete_user(self, user_id: str) -> AdapterResult:
        """
        Delete a user.
        
        Args:
            user_id: The user's ID
        
        Returns:
            AdapterResult with success/failure
        """
        pass
    
    # ================================================================
    # DEVICE MANAGEMENT
    # ================================================================
    
    @abstractmethod
    async def list_devices(
        self,
        page: int = 1,
        page_size: int = 50,
        user_id: Optional[str] = None,
    ) -> AdapterResult:
        """
        List all devices.
        
        Args:
            page: Page number
            page_size: Results per page
            user_id: Optional filter by user
        
        Returns:
            AdapterResult containing VoIPDeviceList
        """
        pass
    
    @abstractmethod
    async def get_device(self, device_id: str) -> AdapterResult:
        """
        Get a single device by ID.
        
        Returns:
            AdapterResult containing VoIPDevice
        """
        pass
    
    @abstractmethod
    async def create_device(self, device_data: VoIPDeviceCreate) -> AdapterResult:
        """
        Create/provision a new device.
        
        Returns:
            AdapterResult containing created VoIPDevice
        """
        pass
    
    @abstractmethod
    async def delete_device(self, device_id: str) -> AdapterResult:
        """
        Delete/deprovision a device.
        
        Returns:
            AdapterResult with success/failure
        """
        pass
    
    # ================================================================
    # CALL QUEUES (Optional - not all providers support)
    # ================================================================
    
    async def list_call_queues(self) -> AdapterResult:
        """List all call queues. Override if provider supports."""
        return AdapterResult.fail(
            code="NOT_SUPPORTED",
            message=f"{self.PROVIDER_NAME} does not support call queues"
        )
    
    async def get_call_queue(self, queue_id: str) -> AdapterResult:
        """Get a call queue. Override if provider supports."""
        return AdapterResult.fail(
            code="NOT_SUPPORTED",
            message=f"{self.PROVIDER_NAME} does not support call queues"
        )
    
    # ================================================================
    # CALL CONTROL (Optional - not all providers support)
    # ================================================================
    
    async def get_active_calls(
        self,
        user_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> AdapterResult:
        """Get list of active calls. Override if provider supports."""
        return AdapterResult.fail(
            code="NOT_SUPPORTED",
            message=f"{self.PROVIDER_NAME} does not support call control"
        )
    
    async def get_call(self, call_id: str) -> AdapterResult:
        """Get details of a specific call. Override if provider supports."""
        return AdapterResult.fail(
            code="NOT_SUPPORTED",
            message=f"{self.PROVIDER_NAME} does not support call control"
        )
    
    async def transfer_call(
        self,
        call_id: str,
        request: TransferCallRequest
    ) -> AdapterResult:
        """Transfer a call. Override if provider supports."""
        return AdapterResult.fail(
            code="NOT_SUPPORTED",
            message=f"{self.PROVIDER_NAME} does not support call control"
        )
    
    async def hold_call(self, call_id: str) -> AdapterResult:
        """Put a call on hold. Override if provider supports."""
        return AdapterResult.fail(
            code="NOT_SUPPORTED",
            message=f"{self.PROVIDER_NAME} does not support call control"
        )
    
    async def resume_call(self, call_id: str) -> AdapterResult:
        """Resume a held call. Override if provider supports."""
        return AdapterResult.fail(
            code="NOT_SUPPORTED",
            message=f"{self.PROVIDER_NAME} does not support call control"
        )
    
    async def mute_call(self, call_id: str) -> AdapterResult:
        """Mute audio for a call. Override if provider supports."""
        return AdapterResult.fail(
            code="NOT_SUPPORTED",
            message=f"{self.PROVIDER_NAME} does not support call control"
        )
    
    async def unmute_call(self, call_id: str) -> AdapterResult:
        """Unmute audio for a call. Override if provider supports."""
        return AdapterResult.fail(
            code="NOT_SUPPORTED",
            message=f"{self.PROVIDER_NAME} does not support call control"
        )
    
    async def hangup_call(self, call_id: str) -> AdapterResult:
        """End/terminate a call. Override if provider supports."""
        return AdapterResult.fail(
            code="NOT_SUPPORTED",
            message=f"{self.PROVIDER_NAME} does not support call control"
        )
    
    async def create_conference(
        self,
        request: ConferenceRequest
    ) -> AdapterResult:
        """Create a conference call. Override if provider supports."""
        return AdapterResult.fail(
            code="NOT_SUPPORTED",
            message=f"{self.PROVIDER_NAME} does not support call control"
        )
    
    async def add_to_conference(
        self,
        conference_id: str,
        call_id: str
    ) -> AdapterResult:
        """Add a call to an existing conference. Override if provider supports."""
        return AdapterResult.fail(
            code="NOT_SUPPORTED",
            message=f"{self.PROVIDER_NAME} does not support call control"
        )
    
    async def remove_from_conference(
        self,
        conference_id: str,
        call_id: str
    ) -> AdapterResult:
        """Remove a call from a conference. Override if provider supports."""
        return AdapterResult.fail(
            code="NOT_SUPPORTED",
            message=f"{self.PROVIDER_NAME} does not support call control"
        )
    
    async def start_recording(
        self,
        call_id: str,
        request: Optional[RecordingRequest] = None
    ) -> AdapterResult:
        """Start recording a call. Override if provider supports."""
        return AdapterResult.fail(
            code="NOT_SUPPORTED",
            message=f"{self.PROVIDER_NAME} does not support call control"
        )
    
    async def stop_recording(self, call_id: str) -> AdapterResult:
        """Stop recording a call. Override if provider supports."""
        return AdapterResult.fail(
            code="NOT_SUPPORTED",
            message=f"{self.PROVIDER_NAME} does not support call control"
        )
    
    async def park_call(self, call_id: str) -> AdapterResult:
        """Park a call. Override if provider supports."""
        return AdapterResult.fail(
            code="NOT_SUPPORTED",
            message=f"{self.PROVIDER_NAME} does not support call control"
        )
    
    async def unpark_call(self, park_code: str) -> AdapterResult:
        """Retrieve a parked call. Override if provider supports."""
        return AdapterResult.fail(
            code="NOT_SUPPORTED",
            message=f"{self.PROVIDER_NAME} does not support call control"
        )
    
    # ================================================================
    # CALL HISTORY (CDR) - Optional
    # ================================================================
    
    async def get_call_history(
        self,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> AdapterResult:
        """Get call history (CDR). Override if provider supports."""
        return AdapterResult.fail(
            code="NOT_SUPPORTED",
            message=f"{self.PROVIDER_NAME} does not support call history"
        )
    
    # ================================================================
    # RECORDINGS - Optional
    # ================================================================
    
    async def get_recording(self, call_id: str, user_id: Optional[str] = None) -> AdapterResult:
        """Get recording for a call. Override if provider supports."""
        return AdapterResult.fail(
            code="NOT_SUPPORTED",
            message=f"{self.PROVIDER_NAME} does not support recordings"
        )
    
    # ================================================================
    # PHONE NUMBERS - Optional
    # ================================================================
    
    async def list_phone_numbers(
        self,
        page: int = 1,
        page_size: int = 50,
        assigned: Optional[bool] = None,
    ) -> AdapterResult:
        """List phone numbers. Override if provider supports."""
        return AdapterResult.fail(
            code="NOT_SUPPORTED",
            message=f"{self.PROVIDER_NAME} does not support phone number management"
        )
    
    async def get_phone_number(self, number_id: str) -> AdapterResult:
        """Get a specific phone number. Override if provider supports."""
        return AdapterResult.fail(
            code="NOT_SUPPORTED",
            message=f"{self.PROVIDER_NAME} does not support phone number management"
        )
    
    # ================================================================
    # VOICEMAIL - Optional
    # ================================================================
    
    async def list_voicemails(
        self,
        user_id: str,
        folder: str = "inbox",
        page: int = 1,
        page_size: int = 50,
    ) -> AdapterResult:
        """List voicemails for a user. Override if provider supports."""
        return AdapterResult.fail(
            code="NOT_SUPPORTED",
            message=f"{self.PROVIDER_NAME} does not support voicemail"
        )
    
    async def get_voicemail(self, voicemail_id: str, user_id: str) -> AdapterResult:
        """Get a specific voicemail. Override if provider supports."""
        return AdapterResult.fail(
            code="NOT_SUPPORTED",
            message=f"{self.PROVIDER_NAME} does not support voicemail"
        )
    
    async def delete_voicemail(self, voicemail_id: str, user_id: str) -> AdapterResult:
        """Delete a voicemail. Override if provider supports."""
        return AdapterResult.fail(
            code="NOT_SUPPORTED",
            message=f"{self.PROVIDER_NAME} does not support voicemail"
        )
    
    # ================================================================
    # MEETINGS - Optional
    # ================================================================
    
    async def create_meeting(
        self,
        user_id: str,
        name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        duration: Optional[int] = None,
    ) -> AdapterResult:
        """Create a meeting. Override if provider supports."""
        return AdapterResult.fail(
            code="NOT_SUPPORTED",
            message=f"{self.PROVIDER_NAME} does not support meetings"
        )
    
    async def get_meeting(self, meeting_id: str) -> AdapterResult:
        """Get meeting details. Override if provider supports."""
        return AdapterResult.fail(
            code="NOT_SUPPORTED",
            message=f"{self.PROVIDER_NAME} does not support meetings"
        )
    
    async def list_meetings(
        self,
        user_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> AdapterResult:
        """List meetings. Override if provider supports."""
        return AdapterResult.fail(
            code="NOT_SUPPORTED",
            message=f"{self.PROVIDER_NAME} does not support meetings"
        )
    
    async def delete_meeting(self, meeting_id: str) -> AdapterResult:
        """Delete a meeting. Override if provider supports."""
        return AdapterResult.fail(
            code="NOT_SUPPORTED",
            message=f"{self.PROVIDER_NAME} does not support meetings"
        )
    
    # ================================================================
    # HELPER METHODS
    # ================================================================
    
    def _build_metadata(self, raw_id: str, raw_data: Dict) -> Dict:
        """Build provider metadata dict for responses."""
        return {
            "provider_type": self.PROVIDER_TYPE,
            "raw_id": raw_id,
            "raw_data": raw_data,
        }

