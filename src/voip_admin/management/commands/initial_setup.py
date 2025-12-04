"""
One-time setup command that runs migrations, creates superuser, and sets up mock connection.
This can be run automatically on first deploy or manually.

Usage: python manage.py initial_setup
"""
import os
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Run initial setup: migrations, superuser, and mock connection'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-superuser',
            action='store_true',
            help='Skip superuser creation if it already exists',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('\n=== Running Initial Setup ===\n'))

        # Run migrations
        self.stdout.write('Running migrations...')
        try:
            call_command('migrate', verbosity=0)
            self.stdout.write(self.style.SUCCESS('✓ Migrations completed'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Migration failed: {e}'))
            return

        # Create superuser if it doesn't exist
        if not options['skip_superuser']:
            if not User.objects.filter(is_superuser=True).exists():
                self.stdout.write('Creating superuser...')
                try:
                    # Use environment variables or defaults
                    username = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
                    email = os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
                    password = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'admin123')
                    
                    User.objects.create_superuser(username, email, password)
                    self.stdout.write(self.style.SUCCESS(f'✓ Superuser created: {username}'))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'⚠ Superuser creation skipped: {e}'))
            else:
                self.stdout.write(self.style.SUCCESS('✓ Superuser already exists'))

        # Setup mock connection
        self.stdout.write('Setting up mock connection...')
        try:
            call_command('setup_mock_connection', verbosity=1)
            self.stdout.write(self.style.SUCCESS('✓ Mock connection created'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Mock connection setup failed: {e}'))

        self.stdout.write(self.style.SUCCESS('\n=== Setup Complete ===\n'))

