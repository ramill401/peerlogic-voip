"""
NetSapiens VoIP Adapter.

Implements the BaseVoIPAdapter interface for NetSapiens UCaaS platform.

NetSapiens API Documentation: https://docs.netsapiens.com/
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

import httpx

from src.voip.adapters.base import (
    BaseVoIPAdapter, 
    AdapterConfig, 
    AdapterResult,
)
from src.voip.models.schemas import (
    VoIPUser, VoIPUserCreate, VoIPUserUpdate, VoIPUserList,
    VoIPDevice, VoIPDeviceCreate, VoIPDeviceList,
    VoIPCallQueue,
    UserStatus, DeviceStatus, DeviceType,
    ProviderMetadata,
)


logger = logging.getLogger("voip.adapters.netsapiens")


class NetSapiensAdapter(BaseVoIPAdapter):
    """
    Adapter for NetSapiens UCaaS platform.
    
    NetSapiens uses:
    - OAuth 2.0 for authentication
    - REST API with JSON responses
    - Terminology: subscribers (users), devices, domains, etc.
    """
    
    PROVIDER_TYPE = "netsapiens"
    PROVIDER_NAME = "NetSapiens"
    
    def __init__(self, config: AdapterConfig):
        super().__init__(config)
        
        # NetSapiens-specific config
        self.domain = config.config.get("domain", "")
        self.territory = config.config.get("territory", "")
        self.client_id = config.credentials.get("client_id", "")
        self.client_secret = config.credentials.get("client_secret", "")
        
        # Token storage (refreshed via OAuth)
        self._access_token: Optional[str] = None
        self._token_expires: Optional[datetime] = None
    
    # ================================================================
    # CONNECTION MANAGEMENT
    # ================================================================
    
    async def connect(self) -> AdapterResult:
        """Initialize connection and authenticate with NetSapiens."""
        try:
            # Create HTTP client
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                headers={"Content-Type": "application/json"},
            )
            
            # Get OAuth token
            auth_result = await self._authenticate()
            if not auth_result.success:
                return auth_result
            
            logger.info(f"Connected to NetSapiens domain: {self.domain}")
            return AdapterResult.ok({"status": "connected", "domain": self.domain})
            
        except Exception as e:
            logger.error(f"Failed to connect to NetSapiens: {e}")
            return AdapterResult.fail(
                code="CONNECTION_ERROR",
                message=f"Failed to connect to NetSapiens: {str(e)}"
            )
    
    async def disconnect(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
        logger.info("Disconnected from NetSapiens")
    
    async def health_check(self) -> AdapterResult:
        """Check if connection is healthy."""
        try:
            # Simple API call to verify connection
            response = await self._make_request("GET", "/ns-api/v2/domains")
            if response.success:
                return AdapterResult.ok({"healthy": True})
            return response
        except Exception as e:
            return AdapterResult.fail(
                code="HEALTH_CHECK_FAILED",
                message=str(e)
            )
    
    async def _authenticate(self) -> AdapterResult:
        """
        Authenticate with NetSapiens OAuth.
        
        Supports both grant types:
        - client_credentials: Only requires client_id and client_secret
        - password: Requires client_id, client_secret, username, and password
        """
        try:
            # Determine grant type from credentials
            grant_type = self.config.credentials.get("grant_type", "client_credentials")
            username = self.config.credentials.get("username")
            password = self.config.credentials.get("password")
            
            # Validate credentials based on grant type
            if grant_type == "client_credentials":
                if not (self.client_id and self.client_secret):
                    return AdapterResult.fail(
                        code="AUTH_ERROR",
                        message="Missing required credentials: client_id, client_secret"
                    )
            elif grant_type == "password":
                if not (self.client_id and self.client_secret and username and password):
                    return AdapterResult.fail(
                        code="AUTH_ERROR",
                        message="Missing required credentials: client_id, client_secret, username, password"
                    )
            else:
                return AdapterResult.fail(
                    code="AUTH_ERROR",
                    message=f"Unsupported grant_type: {grant_type}. Supported: client_credentials, password"
                )
            
            # Build OAuth token request
            token_url = f"{self.config.base_url}oauth2/token/"
            token_params = {
                "grant_type": grant_type,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
            
            # Add username/password only for password grant
            if grant_type == "password":
                token_params["username"] = username
                token_params["password"] = password
            
            # Request access token
            # Note: OAuth2 token endpoint typically expects form-encoded data, not query params
            try:
                response = await self._client.post(
                    token_url,
                    data=token_params,  # Use data= for form-encoded, not params=
                    timeout=self.config.timeout,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                
                if response.status_code != 200:
                    error_body = response.text
                    logger.error(f"OAuth token request failed: {response.status_code} - {error_body}")
                    try:
                        error_json = response.json()
                        error_msg = error_json.get("error_description") or error_json.get("error") or error_body
                    except:
                        error_msg = error_body
                    return AdapterResult.fail(
                        code="AUTH_ERROR",
                        message=f"OAuth authentication failed: {response.status_code} - {error_msg}",
                        details={"response": error_body, "status_code": response.status_code}
                    )
                
                token_data = response.json()
                self._access_token = token_data.get("access_token")
                
                # Store token expiration if provided
                expires_in = token_data.get("expires_in")
                if expires_in:
                    from datetime import timedelta
                    self._token_expires = datetime.now() + timedelta(seconds=expires_in)
                
                logger.info("Authenticated with NetSapiens (OAuth)")
                return AdapterResult.ok({"authenticated": True})
                
            except httpx.TimeoutException:
                return AdapterResult.fail(
                    code="AUTH_TIMEOUT",
                    message="OAuth token request timed out"
                )
            except Exception as e:
                logger.error(f"OAuth token request failed: {e}")
                return AdapterResult.fail(
                    code="AUTH_ERROR",
                    message=f"OAuth token request failed: {str(e)}"
                )
                
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return AdapterResult.fail(
                code="AUTH_ERROR",
                message=f"Authentication failed: {str(e)}"
            )
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Dict = None,
        json_data: Dict = None,
    ) -> AdapterResult:
        """
        Make an authenticated request to NetSapiens API.
        """
        if not self._client:
            return AdapterResult.fail(
                code="NOT_CONNECTED",
                message="Adapter not connected. Call connect() first."
            )
        
        # Check if token is expired and refresh if needed
        if self._token_expires and datetime.now() >= self._token_expires:
            logger.info("Access token expired, re-authenticating...")
            auth_result = await self._authenticate()
            if not auth_result.success:
                return auth_result
        
        headers = {}
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        
        try:
            response = await self._client.request(
                method=method,
                url=endpoint,
                params=params,
                json=json_data,
                headers=headers,
            )
            
            # Check for HTTP errors
            if response.status_code >= 400:
                error_body = response.text
                logger.error(f"NetSapiens API error: {response.status_code} - {error_body}")
                return AdapterResult.fail(
                    code=f"HTTP_{response.status_code}",
                    message=f"API request failed: {response.status_code}",
                    details={"response": error_body}
                )
            
            # Parse JSON response
            data = response.json() if response.text else {}
            return AdapterResult.ok(data)
            
        except httpx.TimeoutException:
            return AdapterResult.fail(
                code="TIMEOUT",
                message="Request timed out"
            )
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return AdapterResult.fail(
                code="REQUEST_ERROR",
                message=str(e)
            )
    
    # ================================================================
    # USER MANAGEMENT
    # ================================================================
    
    async def list_users(
        self,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
        status: Optional[str] = None,
    ) -> AdapterResult:
        """List NetSapiens subscribers (users)."""
        
        # Build query parameters
        params = {
            "domain": self.domain,
            "limit": page_size,
            "offset": (page - 1) * page_size,
        }
        
        if search:
            params["search"] = search
        
        # Make API request
        result = await self._make_request(
            "GET",
            "/ns-api/v2/subscribers",
            params=params
        )
        
        if not result.success:
            return result
        
        # Transform NetSapiens response to universal format
        raw_users = result.data.get("subscribers", [])
        users = [self._transform_user(u) for u in raw_users]
        
        total = result.data.get("total", len(users))
        
        return AdapterResult.ok(VoIPUserList(
            items=users,
            total=total,
            page=page,
            page_size=page_size,
            has_more=(page * page_size) < total
        ))
    
    async def get_user(self, user_id: str) -> AdapterResult:
        """Get a single subscriber by ID."""
        
        result = await self._make_request(
            "GET",
            f"/ns-api/v2/subscribers/{user_id}",
            params={"domain": self.domain}
        )
        
        if not result.success:
            return result
        
        user = self._transform_user(result.data)
        return AdapterResult.ok(user)
    
    async def create_user(self, user_data: VoIPUserCreate) -> AdapterResult:
        """Create a new subscriber in NetSapiens."""
        
        # Transform to NetSapiens format
        ns_data = {
            "domain": self.domain,
            "user": user_data.username,
            "email": user_data.email,
            "first_name": user_data.first_name or "",
            "last_name": user_data.last_name or "",
            "subscriber_type": "standard",
        }
        
        if user_data.extension:
            ns_data["extension"] = user_data.extension
        
        if user_data.password:
            ns_data["password"] = user_data.password
        
        result = await self._make_request(
            "POST",
            "/ns-api/v2/subscribers",
            json_data=ns_data
        )
        
        if not result.success:
            return result
        
        user = self._transform_user(result.data)
        return AdapterResult.ok(user)
    
    async def update_user(
        self, 
        user_id: str, 
        user_data: VoIPUserUpdate
    ) -> AdapterResult:
        """Update a subscriber in NetSapiens."""
        
        # Build update payload (only include non-None fields)
        ns_data = {"domain": self.domain}
        
        if user_data.email is not None:
            ns_data["email"] = user_data.email
        if user_data.first_name is not None:
            ns_data["first_name"] = user_data.first_name
        if user_data.last_name is not None:
            ns_data["last_name"] = user_data.last_name
        if user_data.extension is not None:
            ns_data["extension"] = user_data.extension
        
        result = await self._make_request(
            "PUT",
            f"/ns-api/v2/subscribers/{user_id}",
            json_data=ns_data
        )
        
        if not result.success:
            return result
        
        user = self._transform_user(result.data)
        return AdapterResult.ok(user)
    
    async def delete_user(self, user_id: str) -> AdapterResult:
        """Delete a subscriber from NetSapiens."""
        
        result = await self._make_request(
            "DELETE",
            f"/ns-api/v2/subscribers/{user_id}",
            params={"domain": self.domain}
        )
        
        if not result.success:
            return result
        
        return AdapterResult.ok({"deleted": True, "user_id": user_id})
    
    def _transform_user(self, ns_user: Dict) -> VoIPUser:
        """Transform NetSapiens subscriber to universal VoIPUser."""
        
        # Map NetSapiens status to universal status
        status_map = {
            "active": UserStatus.ACTIVE,
            "inactive": UserStatus.INACTIVE,
            "suspended": UserStatus.SUSPENDED,
        }
        
        return VoIPUser(
            id=ns_user.get("user_id") or ns_user.get("user", ""),
            username=ns_user.get("user", ""),
            email=ns_user.get("email"),
            first_name=ns_user.get("first_name"),
            last_name=ns_user.get("last_name"),
            display_name=ns_user.get("display_name"),
            extension=ns_user.get("extension"),
            did=ns_user.get("did"),
            status=status_map.get(ns_user.get("status", "active"), UserStatus.ACTIVE),
            department=ns_user.get("department"),
            site=ns_user.get("site"),
            has_voicemail=ns_user.get("voicemail_enabled", True),
            created_at=self._parse_datetime(ns_user.get("created_at")),
            updated_at=self._parse_datetime(ns_user.get("updated_at")),
            provider_metadata=ProviderMetadata(
                provider_type=self.PROVIDER_TYPE,
                raw_id=ns_user.get("user_id", ns_user.get("user", "")),
                raw_data=ns_user
            )
        )
    
    # ================================================================
    # DEVICE MANAGEMENT
    # ================================================================
    
    async def list_devices(
        self,
        page: int = 1,
        page_size: int = 50,
        user_id: Optional[str] = None,
    ) -> AdapterResult:
        """List NetSapiens devices."""
        
        params = {
            "domain": self.domain,
            "limit": page_size,
            "offset": (page - 1) * page_size,
        }
        
        if user_id:
            params["user"] = user_id
        
        result = await self._make_request(
            "GET",
            "/ns-api/v2/devices",
            params=params
        )
        
        if not result.success:
            return result
        
        raw_devices = result.data.get("devices", [])
        devices = [self._transform_device(d) for d in raw_devices]
        
        total = result.data.get("total", len(devices))
        
        return AdapterResult.ok(VoIPDeviceList(
            items=devices,
            total=total,
            page=page,
            page_size=page_size,
            has_more=(page * page_size) < total
        ))
    
    async def get_device(self, device_id: str) -> AdapterResult:
        """Get a single device."""
        
        result = await self._make_request(
            "GET",
            f"/ns-api/v2/devices/{device_id}",
            params={"domain": self.domain}
        )
        
        if not result.success:
            return result
        
        device = self._transform_device(result.data)
        return AdapterResult.ok(device)
    
    async def create_device(self, device_data: VoIPDeviceCreate) -> AdapterResult:
        """Create/provision a device in NetSapiens."""
        
        ns_data = {
            "domain": self.domain,
            "mac_address": device_data.mac_address,
            "device_name": device_data.name,
            "device_type": self._to_ns_device_type(device_data.device_type),
        }
        
        if device_data.user_id:
            ns_data["user"] = device_data.user_id
        if device_data.manufacturer:
            ns_data["manufacturer"] = device_data.manufacturer
        if device_data.model:
            ns_data["model"] = device_data.model
        
        result = await self._make_request(
            "POST",
            "/ns-api/v2/devices",
            json_data=ns_data
        )
        
        if not result.success:
            return result
        
        device = self._transform_device(result.data)
        return AdapterResult.ok(device)
    
    async def delete_device(self, device_id: str) -> AdapterResult:
        """Delete/deprovision a device."""
        
        result = await self._make_request(
            "DELETE",
            f"/ns-api/v2/devices/{device_id}",
            params={"domain": self.domain}
        )
        
        if not result.success:
            return result
        
        return AdapterResult.ok({"deleted": True, "device_id": device_id})
    
    def _transform_device(self, ns_device: Dict) -> VoIPDevice:
        """Transform NetSapiens device to universal VoIPDevice."""
        
        return VoIPDevice(
            id=ns_device.get("device_id", ns_device.get("mac_address", "")),
            name=ns_device.get("device_name", ""),
            device_type=self._from_ns_device_type(ns_device.get("device_type")),
            user_id=ns_device.get("user"),
            extension=ns_device.get("extension"),
            mac_address=ns_device.get("mac_address"),
            ip_address=ns_device.get("ip_address"),
            manufacturer=ns_device.get("manufacturer"),
            model=ns_device.get("model"),
            firmware_version=ns_device.get("firmware"),
            status=self._map_device_status(ns_device.get("status")),
            last_seen=self._parse_datetime(ns_device.get("last_seen")),
            provider_metadata=ProviderMetadata(
                provider_type=self.PROVIDER_TYPE,
                raw_id=ns_device.get("device_id", ns_device.get("mac_address", "")),
                raw_data=ns_device
            )
        )
    
    # ================================================================
    # HELPER METHODS
    # ================================================================
    
    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """Parse datetime from various formats."""
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
    
    def _to_ns_device_type(self, device_type: DeviceType) -> str:
        """Convert universal device type to NetSapiens format."""
        type_map = {
            DeviceType.DESK_PHONE: "sip_phone",
            DeviceType.SOFTPHONE: "softphone",
            DeviceType.MOBILE_APP: "mobile",
            DeviceType.WEBRTC: "webrtc",
            DeviceType.ATA: "ata",
        }
        return type_map.get(device_type, "sip_phone")
    
    def _from_ns_device_type(self, ns_type: str) -> DeviceType:
        """Convert NetSapiens device type to universal format."""
        type_map = {
            "sip_phone": DeviceType.DESK_PHONE,
            "softphone": DeviceType.SOFTPHONE,
            "mobile": DeviceType.MOBILE_APP,
            "webrtc": DeviceType.WEBRTC,
            "ata": DeviceType.ATA,
        }
        return type_map.get(ns_type, DeviceType.OTHER)
    
    def _map_device_status(self, ns_status: str) -> DeviceStatus:
        """Map NetSapiens device status to universal status."""
        status_map = {
            "online": DeviceStatus.ONLINE,
            "offline": DeviceStatus.OFFLINE,
            "busy": DeviceStatus.BUSY,
            "registered": DeviceStatus.ONLINE,
            "unregistered": DeviceStatus.OFFLINE,
        }
        return status_map.get(ns_status, DeviceStatus.UNKNOWN)

