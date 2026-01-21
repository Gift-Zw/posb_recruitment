"""
WSGI config for POSB Recruitment Portal project.
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'posb_recruitment.settings')

application = get_wsgi_application()
