"""
Management command to create HR staff users.
Usage: python manage.py create_hr_staff email@posb.com "First Name" "Last Name"
"""
from django.core.management.base import BaseCommand, CommandError
from accounts.models import User


class Command(BaseCommand):
    help = 'Create an HR staff user (bypasses OTP verification)'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email address for HR staff')
        parser.add_argument('--first-name', type=str, default='', help='First name')
        parser.add_argument('--last-name', type=str, default='', help='Last name')
        parser.add_argument('--password', type=str, help='Password (will prompt if not provided)')
        parser.add_argument('--superuser', action='store_true', help='Create as superuser')

    def handle(self, *args, **options):
        email = options['email'].lower()
        first_name = options['first_name']
        last_name = options['last_name']
        is_superuser = options['superuser']
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            raise CommandError(f'User with email {email} already exists.')
        
        # Get password
        password = options.get('password')
        if not password:
            from getpass import getpass
            password = getpass('Password: ')
            password_confirm = getpass('Password (again): ')
            if password != password_confirm:
                raise CommandError('Passwords do not match.')
        
        # Create user
        if is_superuser:
            user = User.objects.create_superuser(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_hr_staff=True  # HR staff flag
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created superuser: {email}')
            )
        else:
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_hr_staff=True,  # HR staff flag
                is_verified=True,  # HR staff bypass OTP
                is_active=True,
                is_staff=True  # Staff access for admin panel
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created HR staff: {email}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nUser Details:\n'
                f'  Email: {user.email}\n'
                f'  Name: {user.get_full_name()}\n'
                f'  HR Staff: {user.is_hr_staff}\n'
                f'  Staff: {user.is_staff}\n'
                f'  Superuser: {user.is_superuser}\n'
                f'  Verified: {user.is_verified}\n'
            )
        )
