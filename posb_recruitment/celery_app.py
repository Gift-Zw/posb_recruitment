"""
Celery configuration for POSB Recruitment Portal.
CELERY REMOVED - This file is kept for future reference.
To re-enable Celery:
1. Install celery and redis: pip install celery redis
2. Uncomment the import in posb_recruitment/__init__.py
3. Uncomment the Celery settings in posb_recruitment/settings.py
4. Convert task functions back to @shared_task decorators
5. Change all task() calls back to task.delay() calls
"""
# import os
# import logging
# from celery import Celery
# 
# logger = logging.getLogger(__name__)
# 
# # Set the default Django settings module for the 'celery' program.
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'posb_recruitment.settings')
# 
# app = Celery('posb_recruitment')
# 
# # Using a string here means the worker doesn't have to serialize
# # the configuration object to child processes.
# app.config_from_object('django.conf:settings', namespace='CELERY')
# 
# # Load task modules from all registered Django apps (tasks.py).
# try:
#     app.autodiscover_tasks()
# except Exception as e:
#     # Log but don't fail if Celery can't connect (e.g., Redis not running)
#     logger.warning(f'Celery autodiscover failed (this is OK if Redis is not running): {e}')
# 
# @app.task(bind=True, ignore_result=True)
# def debug_task(self):
#     print(f'Request: {self.request!r}')
