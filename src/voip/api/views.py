"""
REST API Views for VoIP Admin.

These views provide the HTTP interface for VoIP operations.
"""

import asyncio
import logging
from typing import Optional, Tuple

from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.request import Request

from src.voip_admin.models import Practice, ProviderConnection
from src.voip_admin.permissions import IsPracticeMember, CanManageVoIP, CanAccessConnection


logger = logging.getLogger("voip.api")


def error_response(code: str, message: str, status_code: int = 400) -> JsonResponse:
    """Create a standardized error response."""
    return JsonResponse(
        {"error": {"code": code, "message": message}},
        status=status_code
    )


def run_async(coro):
    """Run an async coroutine in a sync context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def verify_connection_access(request: Request, connection_id: str) -> Tuple[Optional[ProviderConnection], Optional[JsonResponse]]:
    """
    Verify user has access to a connection.
    Returns (connection, None) if access granted, (None, error_response) if denied.
    """
    try:
        conn = ProviderConnection.objects.select_related('practice').get(id=connection_id)
    except ProviderConnection.DoesNotExist:
        return None, error_response(
            "NOT_FOUND",
            f"Connection not found: {connection_id}",
            status_code=404
        )
    
    # Check practice-level access
    permission = CanAccessConnection()
    if not permission.has_object_permission(request, None, conn):
        return None, error_response(
            "FORBIDDEN",
            "You do not have access to this connection",
            status_code=403
        )
    
    return conn, None


# ================================================================
# HEALTH & INFO ENDPOINTS
# ================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def api_health(request: Request) -> JsonResponse:
    """Health check endpoint."""
    return JsonResponse({
        "status": "healthy",
        "service": "peerlogic-voip-admin",
        "version": "1.0.0"
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def api_info(request: Request) -> JsonResponse:
    """API information endpoint."""
    from src.voip.adapters import AdapterRegistry
    
    return JsonResponse({
        "name": "Peerlogic VoIP Admin API",
        "version": "1.0.0",
        "supported_providers": AdapterRegistry.list_supported_providers(),
        "endpoints": {
            "health": "/api/health/",
            "info": "/api/info/",
            "connections": "/api/connections/",
            "users": "/api/connections/{id}/users/",
            "devices": "/api/connections/{id}/devices/",
        }
    })


# ================================================================
# CONNECTION ENDPOINTS
# ================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated, CanManageVoIP])
def list_connections(request: Request) -> JsonResponse:
    """List all provider connections (filtered by practice for multi-tenant)."""
    
    # Multi-tenant filtering: only show connections for user's practice
    # For MVP: superusers see all, regular users see their practice only
    connections = ProviderConnection.objects.select_related(
        'practice', 'provider'
    ).all()
    
    # Filter by practice if user is not superuser
    # TODO: When user-practice relationship model exists, filter by user.practice
    # For now, superusers see all, others see empty (will be fixed when user-practice model added)
    if not request.user.is_superuser:
        # For MVP, return empty list for non-superusers until user-practice model exists
        # In production, this would be: connections = connections.filter(practice=request.user.practice)
        connections = connections.none()
    
    data = [
        {
            "id": str(conn.id),
            "name": conn.name,
            "practice": {
                "id": str(conn.practice.id),
                "name": conn.practice.name,
            },
            "provider": {
                "id": str(conn.provider.id),
                "name": conn.provider.name,
                "type": conn.provider.provider_type,
            },
            "status": conn.status,
            "last_sync_at": conn.last_sync_at.isoformat() if conn.last_sync_at else None,
        }
        for conn in connections
    ]
    
    return JsonResponse({"connections": data, "total": len(data)})


@api_view(['GET'])
@permission_classes([IsAuthenticated, CanManageVoIP])
def get_connection(request: Request, connection_id: str) -> JsonResponse:
    """Get a single connection by ID (with practice-level access control)."""
    
    try:
        conn = ProviderConnection.objects.select_related(
            'practice', 'provider'
        ).get(id=connection_id)
    except ProviderConnection.DoesNotExist:
        return error_response(
            "NOT_FOUND",
            f"Connection not found: {connection_id}",
            status_code=404
        )
    
    # Check practice-level access
    permission = CanAccessConnection()
    if not permission.has_object_permission(request, None, conn):
        return error_response(
            "FORBIDDEN",
            "You do not have access to this connection",
            status_code=403
        )
    
    return JsonResponse({
        "id": str(conn.id),
        "name": conn.name,
        "practice": {
            "id": str(conn.practice.id),
            "name": conn.practice.name,
        },
        "provider": {
            "id": str(conn.provider.id),
            "name": conn.provider.name,
            "type": conn.provider.provider_type,
            "supports_users": conn.provider.supports_users,
            "supports_devices": conn.provider.supports_devices,
            "supports_call_queues": conn.provider.supports_call_queues,
        },
        "config": conn.config,
        "status": conn.status,
        "last_sync_at": conn.last_sync_at.isoformat() if conn.last_sync_at else None,
        "last_error": conn.last_error,
        "created_at": conn.created_at.isoformat(),
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated, CanManageVoIP])
def test_connection(request: Request, connection_id: str) -> JsonResponse:
    """Test a provider connection."""
    from src.voip.services import VoIPService, VoIPServiceError
    
    # Verify connection access
    conn, error = verify_connection_access(request, connection_id)
    if error:
        return error
    
    async def _test():
        service = VoIPService(connection_id, request.user)
        try:
            await service.connect()
            return {"status": "connected", "message": "Connection successful"}
        finally:
            await service.disconnect()
    
    try:
        result = run_async(_test())
        return JsonResponse(result)
    except VoIPServiceError as e:
        return error_response(e.code, e.message, status_code=400)
    except Exception as e:
        logger.exception("Connection test failed")
        return error_response("TEST_FAILED", str(e), status_code=500)


# ================================================================
# USER ENDPOINTS
# ================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated, CanManageVoIP])
def list_users(request: Request, connection_id: str) -> JsonResponse:
    """List users for a connection (with practice-level access control)."""
    from src.voip.services import VoIPService, VoIPServiceError
    
    # Verify connection access
    conn, error = verify_connection_access(request, connection_id)
    if error:
        return error
    
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 50))
    search = request.query_params.get('search')
    
    async def _list():
        service = VoIPService(connection_id, request.user)
        try:
            await service.connect()
            result = await service.list_users(
                page=page,
                page_size=page_size,
                search=search,
            )
            return result
        finally:
            await service.disconnect()
    
    try:
        result = run_async(_list())
        return JsonResponse(result)
    except VoIPServiceError as e:
        return error_response(e.code, e.message, status_code=400)
    except Exception as e:
        logger.exception("Failed to list users")
        return error_response("LIST_FAILED", str(e), status_code=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated, CanManageVoIP])
def get_user(request: Request, connection_id: str, user_id: str) -> JsonResponse:
    """Get a single user."""
    from src.voip.services import VoIPService, VoIPServiceError
    
    # Verify connection access
    conn, error = verify_connection_access(request, connection_id)
    if error:
        return error
    
    async def _get():
        service = VoIPService(connection_id, request.user)
        try:
            await service.connect()
            return await service.get_user(user_id)
        finally:
            await service.disconnect()
    
    try:
        result = run_async(_get())
        return JsonResponse(result)
    except VoIPServiceError as e:
        return error_response(e.code, e.message, status_code=400)
    except Exception as e:
        logger.exception("Failed to get user")
        return error_response("GET_FAILED", str(e), status_code=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated, CanManageVoIP])
def create_user(request: Request, connection_id: str) -> JsonResponse:
    """Create a new user."""
    from src.voip.services import VoIPService, VoIPServiceError
    
    # Verify connection access
    conn, error = verify_connection_access(request, connection_id)
    if error:
        return error
    
    async def _create():
        service = VoIPService(connection_id, request.user)
        try:
            await service.connect()
            return await service.create_user(request.data)
        finally:
            await service.disconnect()
    
    try:
        result = run_async(_create())
        return JsonResponse(result, status=status.HTTP_201_CREATED)
    except VoIPServiceError as e:
        return error_response(e.code, e.message, status_code=400)
    except Exception as e:
        logger.exception("Failed to create user")
        return error_response("CREATE_FAILED", str(e), status_code=500)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated, CanManageVoIP])
def update_user(request: Request, connection_id: str, user_id: str) -> JsonResponse:
    """Update a user."""
    from src.voip.services import VoIPService, VoIPServiceError
    
    # Verify connection access
    conn, error = verify_connection_access(request, connection_id)
    if error:
        return error
    
    async def _update():
        service = VoIPService(connection_id, request.user)
        try:
            await service.connect()
            return await service.update_user(user_id, request.data)
        finally:
            await service.disconnect()
    
    try:
        result = run_async(_update())
        return JsonResponse(result)
    except VoIPServiceError as e:
        return error_response(e.code, e.message, status_code=400)
    except Exception as e:
        logger.exception("Failed to update user")
        return error_response("UPDATE_FAILED", str(e), status_code=500)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, CanManageVoIP])
def delete_user(request: Request, connection_id: str, user_id: str) -> JsonResponse:
    """Delete a user."""
    from src.voip.services import VoIPService, VoIPServiceError
    
    # Verify connection access
    conn, error = verify_connection_access(request, connection_id)
    if error:
        return error
    
    async def _delete():
        service = VoIPService(connection_id, request.user)
        try:
            await service.connect()
            return await service.delete_user(user_id)
        finally:
            await service.disconnect()
    
    try:
        result = run_async(_delete())
        return JsonResponse(result)
    except VoIPServiceError as e:
        return error_response(e.code, e.message, status_code=400)
    except Exception as e:
        logger.exception("Failed to delete user")
        return error_response("DELETE_FAILED", str(e), status_code=500)


# ================================================================
# DEVICE ENDPOINTS
# ================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated, CanManageVoIP])
def list_devices(request: Request, connection_id: str) -> JsonResponse:
    """List devices for a connection."""
    from src.voip.services import VoIPService, VoIPServiceError
    
    # Verify connection access
    conn, error = verify_connection_access(request, connection_id)
    if error:
        return error
    
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 50))
    user_id = request.query_params.get('user_id')
    
    async def _list():
        service = VoIPService(connection_id, request.user)
        try:
            await service.connect()
            return await service.list_devices(
                page=page,
                page_size=page_size,
                user_id=user_id,
            )
        finally:
            await service.disconnect()
    
    try:
        result = run_async(_list())
        return JsonResponse(result)
    except VoIPServiceError as e:
        return error_response(e.code, e.message, status_code=400)
    except Exception as e:
        logger.exception("Failed to list devices")
        return error_response("LIST_FAILED", str(e), status_code=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated, CanManageVoIP])
def get_device(request: Request, connection_id: str, device_id: str) -> JsonResponse:
    """Get a single device."""
    from src.voip.services import VoIPService, VoIPServiceError
    
    # Verify connection access
    conn, error = verify_connection_access(request, connection_id)
    if error:
        return error
    
    async def _get():
        service = VoIPService(connection_id, request.user)
        try:
            await service.connect()
            return await service.get_device(device_id)
        finally:
            await service.disconnect()
    
    try:
        result = run_async(_get())
        return JsonResponse(result)
    except VoIPServiceError as e:
        return error_response(e.code, e.message, status_code=400)
    except Exception as e:
        logger.exception("Failed to get device")
        return error_response("GET_FAILED", str(e), status_code=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated, CanManageVoIP])
def create_device(request: Request, connection_id: str) -> JsonResponse:
    """Create a new device."""
    from src.voip.services import VoIPService, VoIPServiceError
    
    # Verify connection access
    conn, error = verify_connection_access(request, connection_id)
    if error:
        return error
    
    async def _create():
        service = VoIPService(connection_id, request.user)
        try:
            await service.connect()
            return await service.create_device(request.data)
        finally:
            await service.disconnect()
    
    try:
        result = run_async(_create())
        return JsonResponse(result, status=status.HTTP_201_CREATED)
    except VoIPServiceError as e:
        return error_response(e.code, e.message, status_code=400)
    except Exception as e:
        logger.exception("Failed to create device")
        return error_response("CREATE_FAILED", str(e), status_code=500)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, CanManageVoIP])
def delete_device(request: Request, connection_id: str, device_id: str) -> JsonResponse:
    """Delete a device."""
    from src.voip.services import VoIPService, VoIPServiceError
    
    # Verify connection access
    conn, error = verify_connection_access(request, connection_id)
    if error:
        return error
    
    async def _delete():
        service = VoIPService(connection_id, request.user)
        try:
            await service.connect()
            return await service.delete_device(device_id)
        finally:
            await service.disconnect()
    
    try:
        result = run_async(_delete())
        return JsonResponse(result)
    except VoIPServiceError as e:
        return error_response(e.code, e.message, status_code=400)
    except Exception as e:
        logger.exception("Failed to delete device")
        return error_response("DELETE_FAILED", str(e), status_code=500)


# ================================================================
# CALL CONTROL ENDPOINTS
# ================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated, CanManageVoIP])
def list_active_calls(request: Request, connection_id: str) -> JsonResponse:
    """List active calls for a connection."""
    from src.voip.services import VoIPService, VoIPServiceError
    
    # Verify connection access
    conn, error = verify_connection_access(request, connection_id)
    if error:
        return error
    
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 50))
    user_id = request.query_params.get('user_id')
    
    async def _list():
        service = VoIPService(connection_id, request.user)
        try:
            await service.connect()
            return await service.get_active_calls(
                user_id=user_id,
                page=page,
                page_size=page_size,
            )
        finally:
            await service.disconnect()
    
    try:
        result = run_async(_list())
        return JsonResponse(result)
    except VoIPServiceError as e:
        return error_response(e.code, e.message, status_code=400)
    except Exception as e:
        logger.exception("Failed to list active calls")
        return error_response("LIST_FAILED", str(e), status_code=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated, CanManageVoIP])
def get_call(request: Request, connection_id: str, call_id: str) -> JsonResponse:
    """Get details of a specific call."""
    from src.voip.services import VoIPService, VoIPServiceError
    
    # Verify connection access
    conn, error = verify_connection_access(request, connection_id)
    if error:
        return error
    
    async def _get():
        service = VoIPService(connection_id, request.user)
        try:
            await service.connect()
            return await service.get_call(call_id)
        finally:
            await service.disconnect()
    
    try:
        result = run_async(_get())
        return JsonResponse(result)
    except VoIPServiceError as e:
        return error_response(e.code, e.message, status_code=400)
    except Exception as e:
        logger.exception("Failed to get call")
        return error_response("GET_FAILED", str(e), status_code=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated, CanManageVoIP])
def transfer_call(request: Request, connection_id: str, call_id: str) -> JsonResponse:
    """Transfer a call."""
    from src.voip.services import VoIPService, VoIPServiceError
    
    # Verify connection access
    conn, error = verify_connection_access(request, connection_id)
    if error:
        return error
    
    async def _transfer():
        service = VoIPService(connection_id, request.user)
        try:
            await service.connect()
            return await service.transfer_call(call_id, request.data)
        finally:
            await service.disconnect()
    
    try:
        result = run_async(_transfer())
        return JsonResponse(result)
    except VoIPServiceError as e:
        return error_response(e.code, e.message, status_code=400)
    except Exception as e:
        logger.exception("Failed to transfer call")
        return error_response("TRANSFER_FAILED", str(e), status_code=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated, CanManageVoIP])
def hold_call(request: Request, connection_id: str, call_id: str) -> JsonResponse:
    """Put a call on hold."""
    from src.voip.services import VoIPService, VoIPServiceError
    
    # Verify connection access
    conn, error = verify_connection_access(request, connection_id)
    if error:
        return error
    
    async def _hold():
        service = VoIPService(connection_id, request.user)
        try:
            await service.connect()
            return await service.hold_call(call_id)
        finally:
            await service.disconnect()
    
    try:
        result = run_async(_hold())
        return JsonResponse(result)
    except VoIPServiceError as e:
        return error_response(e.code, e.message, status_code=400)
    except Exception as e:
        logger.exception("Failed to hold call")
        return error_response("HOLD_FAILED", str(e), status_code=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated, CanManageVoIP])
def resume_call(request: Request, connection_id: str, call_id: str) -> JsonResponse:
    """Resume a held call."""
    from src.voip.services import VoIPService, VoIPServiceError
    
    # Verify connection access
    conn, error = verify_connection_access(request, connection_id)
    if error:
        return error
    
    async def _resume():
        service = VoIPService(connection_id, request.user)
        try:
            await service.connect()
            return await service.resume_call(call_id)
        finally:
            await service.disconnect()
    
    try:
        result = run_async(_resume())
        return JsonResponse(result)
    except VoIPServiceError as e:
        return error_response(e.code, e.message, status_code=400)
    except Exception as e:
        logger.exception("Failed to resume call")
        return error_response("RESUME_FAILED", str(e), status_code=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated, CanManageVoIP])
def mute_call(request: Request, connection_id: str, call_id: str) -> JsonResponse:
    """Mute audio for a call."""
    from src.voip.services import VoIPService, VoIPServiceError
    
    # Verify connection access
    conn, error = verify_connection_access(request, connection_id)
    if error:
        return error
    
    async def _mute():
        service = VoIPService(connection_id, request.user)
        try:
            await service.connect()
            return await service.mute_call(call_id)
        finally:
            await service.disconnect()
    
    try:
        result = run_async(_mute())
        return JsonResponse(result)
    except VoIPServiceError as e:
        return error_response(e.code, e.message, status_code=400)
    except Exception as e:
        logger.exception("Failed to mute call")
        return error_response("MUTE_FAILED", str(e), status_code=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated, CanManageVoIP])
def unmute_call(request: Request, connection_id: str, call_id: str) -> JsonResponse:
    """Unmute audio for a call."""
    from src.voip.services import VoIPService, VoIPServiceError
    
    # Verify connection access
    conn, error = verify_connection_access(request, connection_id)
    if error:
        return error
    
    async def _unmute():
        service = VoIPService(connection_id, request.user)
        try:
            await service.connect()
            return await service.unmute_call(call_id)
        finally:
            await service.disconnect()
    
    try:
        result = run_async(_unmute())
        return JsonResponse(result)
    except VoIPServiceError as e:
        return error_response(e.code, e.message, status_code=400)
    except Exception as e:
        logger.exception("Failed to unmute call")
        return error_response("UNMUTE_FAILED", str(e), status_code=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated, CanManageVoIP])
def hangup_call(request: Request, connection_id: str, call_id: str) -> JsonResponse:
    """End/terminate a call."""
    from src.voip.services import VoIPService, VoIPServiceError
    
    # Verify connection access
    conn, error = verify_connection_access(request, connection_id)
    if error:
        return error
    
    async def _hangup():
        service = VoIPService(connection_id, request.user)
        try:
            await service.connect()
            return await service.hangup_call(call_id)
        finally:
            await service.disconnect()
    
    try:
        result = run_async(_hangup())
        return JsonResponse(result)
    except VoIPServiceError as e:
        return error_response(e.code, e.message, status_code=400)
    except Exception as e:
        logger.exception("Failed to hangup call")
        return error_response("HANGUP_FAILED", str(e), status_code=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated, CanManageVoIP])
def create_conference(request: Request, connection_id: str) -> JsonResponse:
    """Create a conference call."""
    from src.voip.services import VoIPService, VoIPServiceError
    
    # Verify connection access
    conn, error = verify_connection_access(request, connection_id)
    if error:
        return error
    
    async def _create():
        service = VoIPService(connection_id, request.user)
        try:
            await service.connect()
            return await service.create_conference(request.data)
        finally:
            await service.disconnect()
    
    try:
        result = run_async(_create())
        return JsonResponse(result, status=status.HTTP_201_CREATED)
    except VoIPServiceError as e:
        return error_response(e.code, e.message, status_code=400)
    except Exception as e:
        logger.exception("Failed to create conference")
        return error_response("CONFERENCE_FAILED", str(e), status_code=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated, CanManageVoIP])
def add_to_conference(request: Request, connection_id: str, conference_id: str) -> JsonResponse:
    """Add a call to an existing conference."""
    from src.voip.services import VoIPService, VoIPServiceError
    
    # Verify connection access
    conn, error = verify_connection_access(request, connection_id)
    if error:
        return error
    
    call_id = request.data.get('call_id')
    if not call_id:
        return error_response("MISSING_PARAMETER", "call_id is required", status_code=400)
    
    async def _add():
        service = VoIPService(connection_id, request.user)
        try:
            await service.connect()
            return await service.add_to_conference(conference_id, call_id)
        finally:
            await service.disconnect()
    
    try:
        result = run_async(_add())
        return JsonResponse(result)
    except VoIPServiceError as e:
        return error_response(e.code, e.message, status_code=400)
    except Exception as e:
        logger.exception("Failed to add to conference")
        return error_response("ADD_CONFERENCE_FAILED", str(e), status_code=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated, CanManageVoIP])
def remove_from_conference(request: Request, connection_id: str, conference_id: str, call_id: str) -> JsonResponse:
    """Remove a call from a conference."""
    from src.voip.services import VoIPService, VoIPServiceError
    
    # Verify connection access
    conn, error = verify_connection_access(request, connection_id)
    if error:
        return error
    
    async def _remove():
        service = VoIPService(connection_id, request.user)
        try:
            await service.connect()
            return await service.remove_from_conference(conference_id, call_id)
        finally:
            await service.disconnect()
    
    try:
        result = run_async(_remove())
        return JsonResponse(result)
    except VoIPServiceError as e:
        return error_response(e.code, e.message, status_code=400)
    except Exception as e:
        logger.exception("Failed to remove from conference")
        return error_response("REMOVE_CONFERENCE_FAILED", str(e), status_code=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated, CanManageVoIP])
def start_recording(request: Request, connection_id: str, call_id: str) -> JsonResponse:
    """Start recording a call."""
    from src.voip.services import VoIPService, VoIPServiceError
    
    # Verify connection access
    conn, error = verify_connection_access(request, connection_id)
    if error:
        return error
    
    async def _start():
        service = VoIPService(connection_id, request.user)
        try:
            await service.connect()
            return await service.start_recording(call_id, request.data if request.data else None)
        finally:
            await service.disconnect()
    
    try:
        result = run_async(_start())
        return JsonResponse(result)
    except VoIPServiceError as e:
        return error_response(e.code, e.message, status_code=400)
    except Exception as e:
        logger.exception("Failed to start recording")
        return error_response("RECORDING_START_FAILED", str(e), status_code=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated, CanManageVoIP])
def stop_recording(request: Request, connection_id: str, call_id: str) -> JsonResponse:
    """Stop recording a call."""
    from src.voip.services import VoIPService, VoIPServiceError
    
    # Verify connection access
    conn, error = verify_connection_access(request, connection_id)
    if error:
        return error
    
    async def _stop():
        service = VoIPService(connection_id, request.user)
        try:
            await service.connect()
            return await service.stop_recording(call_id)
        finally:
            await service.disconnect()
    
    try:
        result = run_async(_stop())
        return JsonResponse(result)
    except VoIPServiceError as e:
        return error_response(e.code, e.message, status_code=400)
    except Exception as e:
        logger.exception("Failed to stop recording")
        return error_response("RECORDING_STOP_FAILED", str(e), status_code=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated, CanManageVoIP])
def park_call(request: Request, connection_id: str, call_id: str) -> JsonResponse:
    """Park a call."""
    from src.voip.services import VoIPService, VoIPServiceError
    
    # Verify connection access
    conn, error = verify_connection_access(request, connection_id)
    if error:
        return error
    
    async def _park():
        service = VoIPService(connection_id, request.user)
        try:
            await service.connect()
            return await service.park_call(call_id)
        finally:
            await service.disconnect()
    
    try:
        result = run_async(_park())
        return JsonResponse(result)
    except VoIPServiceError as e:
        return error_response(e.code, e.message, status_code=400)
    except Exception as e:
        logger.exception("Failed to park call")
        return error_response("PARK_FAILED", str(e), status_code=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated, CanManageVoIP])
def unpark_call(request: Request, connection_id: str) -> JsonResponse:
    """Retrieve a parked call."""
    from src.voip.services import VoIPService, VoIPServiceError
    
    # Verify connection access
    conn, error = verify_connection_access(request, connection_id)
    if error:
        return error
    
    park_code = request.data.get('park_code')
    if not park_code:
        return error_response("MISSING_PARAMETER", "park_code is required", status_code=400)
    
    async def _unpark():
        service = VoIPService(connection_id, request.user)
        try:
            await service.connect()
            return await service.unpark_call(park_code)
        finally:
            await service.disconnect()
    
    try:
        result = run_async(_unpark())
        return JsonResponse(result)
    except VoIPServiceError as e:
        return error_response(e.code, e.message, status_code=400)
    except Exception as e:
        logger.exception("Failed to unpark call")
        return error_response("UNPARK_FAILED", str(e), status_code=500)
