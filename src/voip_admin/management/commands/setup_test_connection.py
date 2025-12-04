"""
Management command to create a test NetSapiens connection.

Usage:
    python manage.py setup_test_connection --domain=your.netsapiens.com --client-id=xxx --client-secret=xxx

Or for interactive setup:
    python manage.py setup_test_connection --interactive
"""
import json
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from src.voip_admin.models import (
    VoIPProvider,
    Practice,
    ProviderConnection,
    ProviderCredential,
)


class Command(BaseCommand):
    help = 'Create a test NetSapiens provider connection'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--interactive',
            action='store_true',
            help='Run in interactive mode (prompts for input)',
        )
        parser.add_argument(
            '--domain',
            type=str,
            help='NetSapiens domain (e.g., yourcompany.netsapiens.com)',
        )
        parser.add_argument(
            '--client-id',
            type=str,
            help='OAuth Client ID',
        )
        parser.add_argument(
            '--client-secret',
            type=str,
            help='OAuth Client Secret',
        )
        parser.add_argument(
            '--api-key',
            type=str,
            help='API Key (alternative to OAuth)',
        )
        parser.add_argument(
            '--username',
            type=str,
            help='NetSapiens Username (required for OAuth)',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='NetSapiens Password (required for OAuth)',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('\n=== NetSapiens Connection Setup ===\n'))
        
        # Get or create NetSapiens provider
        provider, created = VoIPProvider.objects.get_or_create(
            provider_type='netsapiens',
            defaults={
                'name': 'NetSapiens',
                'description': 'NetSapiens UCaaS Platform',
                'supports_users': True,
                'supports_devices': True,
                'supports_voicemail': True,
                'supports_call_queues': True,
                'api_base_url_template': 'https://{domain}/ns-api/',
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Created NetSapiens provider'))
        else:
            self.stdout.write(self.style.SUCCESS('✓ Using existing NetSapiens provider'))
        
        # Get or create test practice
        practice, created = Practice.objects.get_or_create(
            external_id='test-practice-001',
            defaults={
                'name': 'Test Dental Practice',
                'primary_email': 'test@example.com',
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Created test practice'))
        else:
            self.stdout.write(self.style.SUCCESS('✓ Using existing test practice'))
        
        # Get configuration
        if options['interactive']:
            domain = input('\nEnter NetSapiens domain (e.g., yourcompany.netsapiens.com): ').strip()
            auth_type = input('Authentication type (oauth/api_key): ').strip().lower()
            
            if auth_type == 'oauth':
                client_id = input('Enter OAuth Client ID: ').strip()
                client_secret = input('Enter OAuth Client Secret: ').strip()
                username = input('Enter NetSapiens Username: ').strip()
                password = input('Enter NetSapiens Password: ').strip()
                credentials = {
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'username': username,
                    'password': password,
                }
                cred_type = 'oauth'
            else:
                api_key = input('Enter API Key: ').strip()
                credentials = {
                    'api_key': api_key,
                }
                cred_type = 'api_key'
        else:
            domain = options.get('domain') or 'demo.netsapiens.com'
            
            if options.get('client_id') and options.get('client_secret'):
                # For OAuth password grant, we also need username and password
                # These should be provided via environment or interactive mode
                username = options.get('username') or input('Enter NetSapiens Username: ').strip()
                password = options.get('password') or input('Enter NetSapiens Password: ').strip()
                credentials = {
                    'client_id': options['client_id'],
                    'client_secret': options['client_secret'],
                    'username': username,
                    'password': password,
                }
                cred_type = 'oauth'
            elif options.get('api_key'):
                credentials = {
                    'api_key': options['api_key'],
                }
                cred_type = 'api_key'
            else:
                # Demo/placeholder credentials
                credentials = {
                    'client_id': 'demo_client_id',
                    'client_secret': 'demo_client_secret',
                }
                cred_type = 'oauth'
                self.stdout.write(self.style.WARNING(
                    '\n⚠ Using placeholder credentials. Run with --interactive to set real ones.'
                ))
        
        # Get admin user for audit trail
        admin_user = User.objects.filter(is_superuser=True).first()
        
        # Create or update provider connection
        connection, created = ProviderConnection.objects.update_or_create(
            practice=practice,
            name='Main Office',
            defaults={
                'provider': provider,
                'config': {
                    'domain': domain,
                    'territory': '',  # Optional: set if needed
                },
                'status': 'pending',
                'created_by': admin_user,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Created provider connection'))
        else:
            self.stdout.write(self.style.SUCCESS('✓ Updated provider connection'))
        
        # Create or update credentials
        # For MVP, we store as JSON bytes (production should encrypt)
        credential_data = json.dumps(credentials).encode('utf-8')
        
        credential, created = ProviderCredential.objects.update_or_create(
            connection=connection,
            defaults={
                'credential_type': cred_type,
                'encrypted_data': credential_data,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Created credentials'))
        else:
            self.stdout.write(self.style.SUCCESS('✓ Updated credentials'))
        
        # Print summary
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 50))
        self.stdout.write(self.style.SUCCESS('CONNECTION CREATED SUCCESSFULLY'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(f'\nConnection ID: {connection.id}')
        self.stdout.write(f'Practice: {practice.name}')
        self.stdout.write(f'Provider: {provider.name}')
        self.stdout.write(f'Domain: {domain}')
        self.stdout.write(f'Auth Type: {cred_type}')
        self.stdout.write(f'Status: {connection.status}')
        
        self.stdout.write(self.style.NOTICE('\n\nTest URLs:'))
        self.stdout.write(f'  List connections: http://127.0.0.1:8000/api/connections/')
        self.stdout.write(f'  Get connection:   http://127.0.0.1:8000/api/connections/{connection.id}/')
        self.stdout.write(f'  Test connection:  POST http://127.0.0.1:8000/api/connections/{connection.id}/test/')
        self.stdout.write(f'  List users:       http://127.0.0.1:8000/api/connections/{connection.id}/users/')
        
        self.stdout.write(self.style.NOTICE('\n\nTo update credentials later, run:'))
        self.stdout.write(f'  python manage.py setup_test_connection --interactive\n')

