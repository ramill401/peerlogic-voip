"""
Create a mock connection for development.

Usage: python manage.py setup_mock_connection
"""

import json
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from src.voip_admin.models import VoIPProvider, Practice, ProviderConnection, ProviderCredential


class Command(BaseCommand):
    help = 'Create a mock provider connection for development'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('\n=== Mock Connection Setup ===\n'))
        
        # Create Mock provider
        provider, created = VoIPProvider.objects.update_or_create(
            provider_type='mock',
            defaults={
                'name': 'Mock Provider (Development)',
                'description': 'Mock adapter for development and testing',
                'supports_users': True,
                'supports_devices': True,
                'supports_voicemail': True,
                'supports_call_queues': True,
                'api_base_url_template': 'http://localhost/mock-api/',
            }
        )
        self.stdout.write(self.style.SUCCESS(f'✓ {"Created" if created else "Updated"} Mock provider'))
        
        # Get or create test practice
        practice, created = Practice.objects.get_or_create(
            external_id='test-practice-001',
            defaults={
                'name': 'Test Dental Practice',
                'primary_email': 'test@example.com',
            }
        )
        self.stdout.write(self.style.SUCCESS(f'✓ {"Created" if created else "Using"} test practice'))
        
        # Get admin user
        admin_user = User.objects.filter(is_superuser=True).first()
        
        # Create mock connection
        connection, created = ProviderConnection.objects.update_or_create(
            practice=practice,
            provider=provider,
            name='Mock Connection',
            defaults={
                'config': {'domain': 'mock.local'},
                'status': 'active',
                'created_by': admin_user,
            }
        )
        self.stdout.write(self.style.SUCCESS(f'✓ {"Created" if created else "Updated"} mock connection'))
        
        # Create mock credentials
        credential, created = ProviderCredential.objects.update_or_create(
            connection=connection,
            defaults={
                'credential_type': 'api_key',
                'encrypted_data': json.dumps({'api_key': 'mock-key'}).encode('utf-8'),
            }
        )
        self.stdout.write(self.style.SUCCESS(f'✓ {"Created" if created else "Updated"} credentials'))
        
        # Print summary
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 50))
        self.stdout.write(self.style.SUCCESS('MOCK CONNECTION READY'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(f'\nConnection ID: {connection.id}')
        self.stdout.write(f'\nTest URLs:')
        self.stdout.write(f'  Health:     http://127.0.0.1:8000/api/health/')
        self.stdout.write(f'  Users:      http://127.0.0.1:8000/api/connections/{connection.id}/users/')
        self.stdout.write(f'  Devices:    http://127.0.0.1:8000/api/connections/{connection.id}/devices/')
        self.stdout.write('')

