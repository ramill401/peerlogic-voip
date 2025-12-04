"""
Mock VoIP Adapter - Returns fake data for development.
"""

import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta

from src.voip.adapters.base import (
    BaseVoIPAdapter,
    AdapterConfig,
    AdapterResult,
)
from src.voip.models import (
    VoIPUser, VoIPUserCreate, VoIPUserUpdate, VoIPUserList,
    VoIPDevice, VoIPDeviceCreate, VoIPDeviceList,
    UserStatus, DeviceStatus, DeviceType,
    ProviderMetadata,
)


logger = logging.getLogger("voip.adapters.mock")


# Sample Users
MOCK_USERS = [
    {"id": "user-001", "username": "jsmith", "email": "john.smith@testdental.com", 
     "first_name": "John", "last_name": "Smith", "extension": "101", 
     "did": "+15551234101", "department": "Front Desk", "status": "active"},
    {"id": "user-002", "username": "mjohnson", "email": "mary.johnson@testdental.com",
     "first_name": "Mary", "last_name": "Johnson", "extension": "102",
     "did": "+15551234102", "department": "Hygiene", "status": "active"},
    {"id": "user-003", "username": "drwilliams", "email": "dr.williams@testdental.com",
     "first_name": "Robert", "last_name": "Williams", "extension": "103",
     "did": "+15551234103", "department": "Dentist", "status": "active"},
    {"id": "user-004", "username": "sbrown", "email": "sarah.brown@testdental.com",
     "first_name": "Sarah", "last_name": "Brown", "extension": "104",
     "did": "+15551234104", "department": "Front Desk", "status": "active"},
    {"id": "user-005", "username": "drdavis", "email": "dr.davis@testdental.com",
     "first_name": "Emily", "last_name": "Davis", "extension": "105",
     "did": "+15551234105", "department": "Dentist", "status": "active"},
    {"id": "user-006", "username": "jgarcia", "email": "jose.garcia@testdental.com",
     "first_name": "Jose", "last_name": "Garcia", "extension": "106",
     "did": "+15551234106", "department": "Billing", "status": "active"},
    {"id": "user-007", "username": "amiller", "email": "amanda.miller@testdental.com",
     "first_name": "Amanda", "last_name": "Miller", "extension": "107",
     "did": "+15551234107", "department": "Hygiene", "status": "inactive"},
    {"id": "user-008", "username": "twang", "email": "tom.wang@testdental.com",
     "first_name": "Tom", "last_name": "Wang", "extension": "108",
     "did": "+15551234108", "department": "IT", "status": "active"},
]

# Sample Devices
MOCK_DEVICES = [
    {"id": "device-001", "name": "Front Desk Phone 1", "device_type": "desk_phone",
     "user_id": "user-001", "mac_address": "AA:BB:CC:DD:EE:01", "manufacturer": "Polycom",
     "model": "VVX 450", "status": "online"},
    {"id": "device-002", "name": "Front Desk Phone 2", "device_type": "desk_phone",
     "user_id": "user-004", "mac_address": "AA:BB:CC:DD:EE:02", "manufacturer": "Polycom",
     "model": "VVX 450", "status": "online"},
    {"id": "device-003", "name": "Hygiene Room 1", "device_type": "desk_phone",
     "user_id": "user-002", "mac_address": "AA:BB:CC:DD:EE:03", "manufacturer": "Yealink",
     "model": "T46U", "status": "online"},
    {"id": "device-004", "name": "Dr. Williams Office", "device_type": "desk_phone",
     "user_id": "user-003", "mac_address": "AA:BB:CC:DD:EE:04", "manufacturer": "Polycom",
     "model": "VVX 601", "status": "offline"},
    {"id": "device-005", "name": "Dr. Davis Office", "device_type": "desk_phone",
     "user_id": "user-005", "mac_address": "AA:BB:CC:DD:EE:05", "manufacturer": "Polycom",
     "model": "VVX 601", "status": "online"},
    {"id": "device-006", "name": "Billing Softphone", "device_type": "softphone",
     "user_id": "user-006", "mac_address": None, "manufacturer": "NetSapiens",
     "model": "Desktop App", "status": "online"},
    {"id": "device-007", "name": "Conference Room", "device_type": "conference",
     "user_id": None, "mac_address": "AA:BB:CC:DD:EE:07", "manufacturer": "Poly",
     "model": "Trio 8500", "status": "online"},
]


class MockAdapter(BaseVoIPAdapter):
    """Mock adapter for development and testing."""
    
    PROVIDER_TYPE = "mock"
    PROVIDER_NAME = "Mock Provider"
    
    def __init__(self, config: AdapterConfig):
        super().__init__(config)
        self._users = {u["id"]: u.copy() for u in MOCK_USERS}
        self._devices = {d["id"]: d.copy() for d in MOCK_DEVICES}
        self._next_user_id = 9
        self._next_device_id = 8
    
    async def connect(self) -> AdapterResult:
        logger.info("Mock adapter connected")
        return AdapterResult.ok({"status": "connected"})
    
    async def disconnect(self) -> None:
        logger.info("Mock adapter disconnected")
    
    async def health_check(self) -> AdapterResult:
        return AdapterResult.ok({"healthy": True})
    
    # ================================================================
    # USER OPERATIONS
    # ================================================================
    
    async def list_users(
        self,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
        status: Optional[str] = None,
    ) -> AdapterResult:
        users = list(self._users.values())
        
        # Filter by search
        if search:
            search = search.lower()
            users = [u for u in users if 
                search in u.get("username", "").lower() or
                search in u.get("email", "").lower() or
                search in u.get("first_name", "").lower() or
                search in u.get("last_name", "").lower() or
                search in u.get("extension", "").lower()
            ]
        
        # Filter by status
        if status:
            users = [u for u in users if u.get("status") == status]
        
        total = len(users)
        start = (page - 1) * page_size
        end = start + page_size
        page_users = users[start:end]
        
        voip_users = [self._to_voip_user(u) for u in page_users]
        
        return AdapterResult.ok(VoIPUserList(
            items=voip_users,
            total=total,
            page=page,
            page_size=page_size,
            has_more=end < total
        ))
    
    async def get_user(self, user_id: str) -> AdapterResult:
        if user_id not in self._users:
            return AdapterResult.fail("NOT_FOUND", f"User not found: {user_id}")
        return AdapterResult.ok(self._to_voip_user(self._users[user_id]))
    
    async def create_user(self, user_data: VoIPUserCreate) -> AdapterResult:
        user_id = f"user-{self._next_user_id:03d}"
        self._next_user_id += 1
        
        new_user = {
            "id": user_id,
            "username": user_data.username,
            "email": user_data.email,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "extension": user_data.extension or str(100 + self._next_user_id),
            "did": f"+1555123{100 + self._next_user_id}",
            "department": user_data.department,
            "status": "active",
        }
        self._users[user_id] = new_user
        
        return AdapterResult.ok(self._to_voip_user(new_user))
    
    async def update_user(self, user_id: str, user_data: VoIPUserUpdate) -> AdapterResult:
        if user_id not in self._users:
            return AdapterResult.fail("NOT_FOUND", f"User not found: {user_id}")
        
        user = self._users[user_id]
        if user_data.email is not None:
            user["email"] = user_data.email
        if user_data.first_name is not None:
            user["first_name"] = user_data.first_name
        if user_data.last_name is not None:
            user["last_name"] = user_data.last_name
        if user_data.extension is not None:
            user["extension"] = user_data.extension
        if user_data.status is not None:
            user["status"] = user_data.status
        
        return AdapterResult.ok(self._to_voip_user(user))
    
    async def delete_user(self, user_id: str) -> AdapterResult:
        if user_id not in self._users:
            return AdapterResult.fail("NOT_FOUND", f"User not found: {user_id}")
        del self._users[user_id]
        return AdapterResult.ok({"deleted": True, "user_id": user_id})
    
    def _to_voip_user(self, data: Dict) -> VoIPUser:
        status_map = {"active": UserStatus.ACTIVE, "inactive": UserStatus.INACTIVE}
        return VoIPUser(
            id=data["id"],
            username=data.get("username", ""),
            email=data.get("email"),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            extension=data.get("extension"),
            did=data.get("did"),
            department=data.get("department"),
            status=status_map.get(data.get("status", "active"), UserStatus.ACTIVE),
            has_voicemail=True,
            created_at=datetime.now() - timedelta(days=30),
            provider_metadata=ProviderMetadata(
                provider_type=self.PROVIDER_TYPE,
                raw_id=data["id"],
                raw_data=data
            )
        )
    
    # ================================================================
    # DEVICE OPERATIONS
    # ================================================================
    
    async def list_devices(
        self,
        page: int = 1,
        page_size: int = 50,
        user_id: Optional[str] = None,
    ) -> AdapterResult:
        devices = list(self._devices.values())
        
        if user_id:
            devices = [d for d in devices if d.get("user_id") == user_id]
        
        total = len(devices)
        start = (page - 1) * page_size
        end = start + page_size
        page_devices = devices[start:end]
        
        voip_devices = [self._to_voip_device(d) for d in page_devices]
        
        return AdapterResult.ok(VoIPDeviceList(
            items=voip_devices,
            total=total,
            page=page,
            page_size=page_size,
            has_more=end < total
        ))
    
    async def get_device(self, device_id: str) -> AdapterResult:
        if device_id not in self._devices:
            return AdapterResult.fail("NOT_FOUND", f"Device not found: {device_id}")
        return AdapterResult.ok(self._to_voip_device(self._devices[device_id]))
    
    async def create_device(self, device_data: VoIPDeviceCreate) -> AdapterResult:
        device_id = f"device-{self._next_device_id:03d}"
        self._next_device_id += 1
        
        new_device = {
            "id": device_id,
            "name": device_data.name,
            "device_type": device_data.device_type.value if hasattr(device_data.device_type, 'value') else device_data.device_type,
            "user_id": device_data.user_id,
            "mac_address": device_data.mac_address,
            "manufacturer": device_data.manufacturer,
            "model": device_data.model,
            "status": "offline",
        }
        self._devices[device_id] = new_device
        
        return AdapterResult.ok(self._to_voip_device(new_device))
    
    async def delete_device(self, device_id: str) -> AdapterResult:
        if device_id not in self._devices:
            return AdapterResult.fail("NOT_FOUND", f"Device not found: {device_id}")
        del self._devices[device_id]
        return AdapterResult.ok({"deleted": True, "device_id": device_id})
    
    def _to_voip_device(self, data: Dict) -> VoIPDevice:
        type_map = {
            "desk_phone": DeviceType.DESK_PHONE,
            "softphone": DeviceType.SOFTPHONE,
            "conference": DeviceType.CONFERENCE,
        }
        status_map = {
            "online": DeviceStatus.ONLINE,
            "offline": DeviceStatus.OFFLINE,
        }
        return VoIPDevice(
            id=data["id"],
            name=data.get("name", ""),
            device_type=type_map.get(data.get("device_type"), DeviceType.OTHER),
            user_id=data.get("user_id"),
            mac_address=data.get("mac_address"),
            manufacturer=data.get("manufacturer"),
            model=data.get("model"),
            status=status_map.get(data.get("status"), DeviceStatus.UNKNOWN),
            last_seen=datetime.now() - timedelta(minutes=5),
            provider_metadata=ProviderMetadata(
                provider_type=self.PROVIDER_TYPE,
                raw_id=data["id"],
                raw_data=data
            )
        )

