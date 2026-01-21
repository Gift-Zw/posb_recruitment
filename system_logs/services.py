"""
System logging service for POSB Recruitment Portal.
Centralized service for creating system log entries.
"""
from .models import SystemLog
import traceback


def log_system_event(
    level='INFO',
    source='SYSTEM',
    message='',
    stack_trace=None,
    module='',
    function='',
    related_user=None,
    metadata=None
):
    """
    Create a system log entry.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        source: Source of log (API, CELERY, INTEGRATION, SYSTEM)
        message: Log message
        stack_trace: Stack trace string (optional)
        module: Module/component name
        function: Function/method name
        related_user: Related user (optional)
        metadata: Additional context data (dict)
    """
    try:
        SystemLog.objects.create(
            level=level,
            source=source,
            message=message,
            stack_trace=stack_trace or '',
            module=module,
            function=function,
            related_user=related_user,
            metadata=metadata or {}
        )
    except Exception as e:
        # Fallback to standard logging if database logging fails
        import logging
        logger = logging.getLogger('posb_recruitment')
        logger.error(f'Failed to create system log: {str(e)}')


def log_exception(exception, source='API', module='', function='', related_user=None, metadata=None):
    """
    Log an exception with full stack trace.
    
    Args:
        exception: Exception instance
        source: Source of log
        module: Module/component name
        function: Function/method name
        related_user: Related user (optional)
        metadata: Additional context data (dict)
    """
    stack_trace = ''.join(traceback.format_exception(type(exception), exception, exception.__traceback__))
    log_system_event(
        level='ERROR',
        source=source,
        message=f'{type(exception).__name__}: {str(exception)}',
        stack_trace=stack_trace,
        module=module,
        function=function,
        related_user=related_user,
        metadata=metadata
    )
