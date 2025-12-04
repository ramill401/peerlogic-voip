"""
Universal VoIP data schemas.

These Pydantic models define the standard format for VoIP entities.
All provider adapters convert their data to these formats.
This ensures the Peerlogic app always works with consistent data
regardless of which VoIP provider is being used.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr


# ============================================================
# ENUMS - Standard values across all providers
# ============================================================

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class DeviceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    UNKNOWN = "unknown"


class DeviceType(str, Enum):
    DESK_PHONE = "desk_phone"
    SOFTPHONE = "softphone"
    MOBILE_APP = "mobile_app"
    WEBRTC = "webrtc"
    ATA = "ata"  # Analog Telephone Adapter
    CONFERENCE = "conference"
    OTHER = "other"


class CallQueueStrategy(str, Enum):
    RING_ALL = "ring_all"
    ROUND_ROBIN = "round_robin"
    LEAST_RECENT = "least_recent"
    FEWEST_CALLS = "fewest_calls"
    RANDOM = "random"
    LINEAR = "linear"


# ============================================================
# BASE MODELS
# ============================================================

class VoIPBaseModel(BaseModel):
    """Base model with common fields."""
    
    class Config:
        # Allow extra fields from providers (we'll ignore them)
        extra = "ignore"
        # Use enum values, not enum objects
        use_enum_values = True


class ProviderMetadata(VoIPBaseModel):
    """
    Stores original provider-specific data.
    Useful for debugging and round-trip operations.
    """
    provider_type: str
    raw_id: str  # Original ID from provider
    raw_data: Dict[str, Any] = Field(default_factory=dict)


# ============================================================
# USER MODELS
# ============================================================

class VoIPUser(VoIPBaseModel):
    """
    Universal representation of a VoIP user/extension.
    
    Maps to:
    - NetSapiens: subscriber
    - RingCentral: extension
    - 8x8: user
    """
    
    # Universal identifier (we generate this)
    id: str
    
    # Basic info
    username: str
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    
    # Extension info
    extension: Optional[str] = None
    did: Optional[str] = None  # Direct Inward Dial (phone number)
    
    # Status
    status: UserStatus = UserStatus.ACTIVE
    
    # Organizational
    department: Optional[str] = None
    site: Optional[str] = None  # Office location
    
    # Capabilities
    has_voicemail: bool = True
    has_sms: bool = False
    has_fax: bool = False
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Provider-specific data
    provider_metadata: Optional[ProviderMetadata] = None
    
    @property
    def full_name(self) -> str:
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.display_name or self.username


class VoIPUserCreate(VoIPBaseModel):
    """Data required to create a new user."""
    
    username: str
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    extension: Optional[str] = None
    password: Optional[str] = None  # Some providers require this
    department: Optional[str] = None
    site: Optional[str] = None


class VoIPUserUpdate(VoIPBaseModel):
    """Data that can be updated on a user."""
    
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    extension: Optional[str] = None
    status: Optional[UserStatus] = None
    department: Optional[str] = None


# ============================================================
# DEVICE MODELS
# ============================================================

class VoIPDevice(VoIPBaseModel):
    """
    Universal representation of a VoIP device/phone.
    
    Maps to:
    - NetSapiens: device
    - RingCentral: device
    - 8x8: endpoint
    """
    
    id: str
    
    # Basic info
    name: str
    device_type: DeviceType = DeviceType.DESK_PHONE
    
    # Association
    user_id: Optional[str] = None  # Which user owns this device
    extension: Optional[str] = None
    
    # Device details
    mac_address: Optional[str] = None
    ip_address: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    firmware_version: Optional[str] = None
    
    # Status
    status: DeviceStatus = DeviceStatus.UNKNOWN
    last_seen: Optional[datetime] = None
    
    # Provider-specific data
    provider_metadata: Optional[ProviderMetadata] = None


class VoIPDeviceCreate(VoIPBaseModel):
    """Data required to create/provision a new device."""
    
    name: str
    device_type: DeviceType = DeviceType.DESK_PHONE
    mac_address: str
    user_id: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None


# ============================================================
# CALL QUEUE MODELS
# ============================================================

class CallQueueMember(VoIPBaseModel):
    """A member of a call queue."""
    
    user_id: str
    priority: int = 1
    is_active: bool = True


class VoIPCallQueue(VoIPBaseModel):
    """
    Universal representation of a call queue/hunt group.
    """
    
    id: str
    name: str
    extension: Optional[str] = None
    
    # Queue behavior
    strategy: CallQueueStrategy = CallQueueStrategy.RING_ALL
    ring_time: int = 20  # Seconds before moving to next
    max_wait_time: int = 300  # Max seconds in queue
    
    # Members
    members: List[CallQueueMember] = Field(default_factory=list)
    
    # Overflow handling
    overflow_destination: Optional[str] = None  # Extension or voicemail
    
    # Status
    is_active: bool = True
    
    # Provider-specific data
    provider_metadata: Optional[ProviderMetadata] = None


# ============================================================
# RESPONSE WRAPPERS
# ============================================================

class PaginatedResponse(VoIPBaseModel):
    """Standard paginated response wrapper."""
    
    items: List[Any]
    total: int
    page: int = 1
    page_size: int = 50
    has_more: bool = False


class VoIPUserList(PaginatedResponse):
    """Paginated list of users."""
    items: List[VoIPUser]


class VoIPDeviceList(PaginatedResponse):
    """Paginated list of devices."""
    items: List[VoIPDevice]


# ============================================================
# ERROR MODELS
# ============================================================

class VoIPError(VoIPBaseModel):
    """Standard error response from adapters."""
    
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    provider_error: Optional[str] = None  # Original error from provider

