"""
Management command to test email configuration.
Usage: python manage.py test_email your-email@example.com
"""
import socket
import sys
from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail, get_connection
from django.conf import settings

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


class Command(BaseCommand):
    help = 'Test email configuration by sending a test email'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email address to send test email to')
        parser.add_argument('--console', action='store_true', help='Use console backend (for testing without SMTP)')
        parser.add_argument('--port', type=int, help='Override SMTP port (try 465 for SSL)')

    def handle(self, *args, **options):
        recipient_email = options['email']
        use_console = options.get('console', False)
        port_override = options.get('port')
        
        self.stdout.write(self.style.WARNING('Testing email configuration...'))
        
        if use_console:
            self.stdout.write(self.style.WARNING('Using console backend (emails will print to console)'))
            email_backend = 'django.core.mail.backends.console.EmailBackend'
        else:
            email_backend = settings.EMAIL_BACKEND
            self.stdout.write(f'EMAIL_BACKEND: {email_backend}')
            self.stdout.write(f'EMAIL_HOST: {settings.EMAIL_HOST}')
            self.stdout.write(f'EMAIL_PORT: {port_override or settings.EMAIL_PORT}')
            self.stdout.write(f'EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}')
            self.stdout.write(f'EMAIL_HOST_USER: {settings.EMAIL_HOST_USER or "(not set)"}')
            self.stdout.write(f'DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}')
        
        self.stdout.write('')
        
        if not use_console and not settings.EMAIL_HOST_USER:
            self.stdout.write(self.style.ERROR('WARNING: EMAIL_HOST_USER is not set!'))
            self.stdout.write(self.style.ERROR('Please set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in your .env file.'))
            self.stdout.write(self.style.WARNING('Or use --console flag to test without SMTP'))
            return
        
        # Test network connectivity first
        if not use_console:
            self.stdout.write('Testing network connectivity...')
            try:
                host = settings.EMAIL_HOST
                port = port_override or settings.EMAIL_PORT
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                sock.close()
                if result != 0:
                    self.stdout.write(self.style.ERROR(f'✗ Cannot connect to {host}:{port}'))
                    self.stdout.write(self.style.ERROR(''))
                    self.stdout.write(self.style.WARNING('Troubleshooting:'))
                    self.stdout.write(self.style.WARNING('1. Check if firewall is blocking the connection'))
                    self.stdout.write(self.style.WARNING('2. Try port 465 with SSL: --port 465 (and set EMAIL_USE_SSL=True in .env)'))
                    self.stdout.write(self.style.WARNING('3. Check if you are behind a proxy/VPN'))
                    self.stdout.write(self.style.WARNING('4. Use --console flag to test email functionality without SMTP'))
                    return
                else:
                    self.stdout.write(self.style.SUCCESS(f'✓ Network connection to {host}:{port} successful'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Network test failed: {str(e)}'))
                self.stdout.write(self.style.WARNING('Use --console flag to test email functionality without SMTP'))
                return
        
        # Try to send email
        try:
            if use_console:
                connection = get_connection(backend=email_backend)
            elif port_override:
                # Create custom connection with port override
                connection = get_connection(
                    backend=email_backend,
                    host=settings.EMAIL_HOST,
                    port=port_override,
                    username=settings.EMAIL_HOST_USER,
                    password=settings.EMAIL_HOST_PASSWORD,
                    use_tls=settings.EMAIL_USE_TLS,
                    use_ssl=getattr(settings, 'EMAIL_USE_SSL', False),
                )
            else:
                connection = None  # Use default settings
            
            send_mail(
                subject='POSB Recruitment Portal - Test Email',
                message='This is a test email from the POSB Recruitment Portal. If you receive this, your email configuration is working correctly!',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                fail_silently=False,
                connection=connection,
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Test email sent successfully to {recipient_email}'))
            if use_console:
                self.stdout.write(self.style.SUCCESS('Check the console output above to see the email content.'))
            else:
                self.stdout.write(self.style.SUCCESS('Please check your inbox (and spam folder) for the test email.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Failed to send email: {str(e)}'))
            self.stdout.write(self.style.ERROR(''))
            self.stdout.write(self.style.ERROR('Common issues:'))
            self.stdout.write(self.style.ERROR('1. Check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in .env'))
            self.stdout.write(self.style.ERROR('2. For Gmail, use an App Password (not your regular password)'))
            self.stdout.write(self.style.ERROR('3. Try port 465 with SSL: --port 465 (and set EMAIL_USE_SSL=True in .env)'))
            self.stdout.write(self.style.ERROR('4. Check firewall/network settings'))
            self.stdout.write(self.style.ERROR('5. Use --console flag to test without SMTP'))
            raise CommandError(f'Email test failed: {str(e)}')
