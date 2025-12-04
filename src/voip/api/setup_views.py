"""
One-time setup endpoint for Railway deployment.
This allows running initial setup via HTTP request.
"""
import logging
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.core.management import call_command
from django.contrib.auth.models import User
from src.voip_admin.models import ProviderConnection

logger = logging.getLogger("voip.api")

@api_view(['POST'])
@permission_classes([AllowAny])  # In production, add proper auth
def run_initial_setup(request):
    """
    Run initial setup: migrations, superuser, and mock connection.
    This is a one-time setup endpoint for Railway deployment.
    """
    try:
        # Run migrations first (this is safe to run multiple times)
        logger.info("Running migrations...")
        call_command('migrate', verbosity=0, interactive=False)
        logger.info("Migrations completed")
        
        # Check if setup already done
        if ProviderConnection.objects.exists():
            connection = ProviderConnection.objects.first()
            return JsonResponse({
                "status": "already_setup",
                "message": "Setup already completed",
                "connection_id": str(connection.id)
            })
        
        # Create superuser if doesn't exist
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123'
            )
            logger.info("Superuser created: admin")
        
        # Setup mock connection
        call_command('setup_mock_connection', verbosity=0)
        
        # Get the connection ID
        connection = ProviderConnection.objects.first()
        
        return JsonResponse({
            "status": "success",
            "message": "Initial setup completed",
            "connection_id": str(connection.id) if connection else None,
            "superuser": {
                "username": "admin",
                "password": "admin123"
            }
        })
        
    except Exception as e:
        logger.exception("Setup failed")
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)

