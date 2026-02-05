"""
Management command to create API keys for the job portal API.
"""
import secrets
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from integrations.models import APIKey

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a new API key for the job portal API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--name',
            type=str,
            required=True,
            help='Descriptive name for this API key (e.g., "D365 Production Key")'
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Username or email of the user creating this key'
        )
        parser.add_argument(
            '--key',
            type=str,
            help='Custom API key value (if not provided, a random key will be generated)'
        )

    def handle(self, *args, **options):
        name = options['name']
        user_identifier = options.get('user')
        custom_key = options.get('key')
        
        # Get user if provided
        created_by = None
        if user_identifier:
            try:
                if '@' in user_identifier:
                    created_by = User.objects.get(email=user_identifier)
                else:
                    created_by = User.objects.get(username=user_identifier)
            except User.DoesNotExist:
                raise CommandError(f'User "{user_identifier}" not found')
        
        # Generate or use custom key
        if custom_key:
            api_key_value = custom_key
        else:
            api_key_value = secrets.token_urlsafe(32)
        
        # Check if key already exists
        if APIKey.objects.filter(key=api_key_value).exists():
            raise CommandError(f'API key already exists. Please use a different key.')
        
        # Create API key
        api_key = APIKey.objects.create(
            name=name,
            key=api_key_value,
            is_active=True,
            created_by=created_by
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ API key created successfully!\n\n'
                f'Name: {api_key.name}\n'
                f'Key: {api_key.key}\n'
                f'Active: {api_key.is_active}\n'
                f'Created: {api_key.created_at}\n'
                f'\n⚠️  IMPORTANT: Save this key securely. It will not be shown again!\n'
                f'Use this key in the X-API-Key header when making requests.\n'
            )
        )
