"""
REST API Views for VoIP Admin.

These views provide the HTTP interface for VoIP operations.
"""

import asyncio
import logging
from typing import Optional

from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.request import Request

from src.voip_admin.models import Practice, ProviderConnection


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
@permission_classes([AllowAny])
def list_connections(request: Request) -> JsonResponse:
    """List all provider connections."""
    
    connections = ProviderConnection.objects.select_related(
        'practice', 'provider'
    ).all()
    
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
@permission_classes([AllowAny])
def get_connection(request: Request, connection_id: str) -> JsonResponse:
    """Get a single connection by ID."""
    
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
@permission_classes([AllowAny])
def test_connection(request: Request, connection_id: str) -> JsonResponse:
    """Test a provider connection."""
    from src.voip.services import VoIPService, VoIPServiceError
    
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
@permission_classes([AllowAny])
def list_users(request: Request, connection_id: str) -> JsonResponse:
    """List users for a connection."""
    from src.voip.services import VoIPService, VoIPServiceError
    
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
@permission_classes([AllowAny])
def get_user(request: Request, connection_id: str, user_id: str) -> JsonResponse:
    """Get a single user."""
    from src.voip.services import VoIPService, VoIPServiceError
    
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
@permission_classes([AllowAny])
def create_user(request: Request, connection_id: str) -> JsonResponse:
    """Create a new user."""
    from src.voip.services import VoIPService, VoIPServiceError
    
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
@permission_classes([AllowAny])
def update_user(request: Request, connection_id: str, user_id: str) -> JsonResponse:
    """Update a user."""
    from src.voip.services import VoIPService, VoIPServiceError
    
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
@permission_classes([AllowAny])
def delete_user(request: Request, connection_id: str, user_id: str) -> JsonResponse:
    """Delete a user."""
    from src.voip.services import VoIPService, VoIPServiceError
    
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
@permission_classes([AllowAny])
def list_devices(request: Request, connection_id: str) -> JsonResponse:
    """List devices for a connection."""
    from src.voip.services import VoIPService, VoIPServiceError
    
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
@permission_classes([AllowAny])
def get_device(request: Request, connection_id: str, device_id: str) -> JsonResponse:
    """Get a single device."""
    from src.voip.services import VoIPService, VoIPServiceError
    
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
@permission_classes([AllowAny])
def create_device(request: Request, connection_id: str) -> JsonResponse:
    """Create a new device."""
    from src.voip.services import VoIPService, VoIPServiceError
    
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
@permission_classes([AllowAny])
def delete_device(request: Request, connection_id: str, device_id: str) -> JsonResponse:
    """Delete a device."""
    from src.voip.services import VoIPService, VoIPServiceError
    
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
