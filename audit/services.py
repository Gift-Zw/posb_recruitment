"""
Audit logging service for POSB Recruitment Portal.
Centralized service for creating audit log entries.
"""
from django.contrib.contenttypes.models import ContentType
from .models import AuditLog


def log_audit_event(
    actor=None,
    action=None,
    action_description='',
    entity=None,
    metadata=None,
    request=None
):
    """
    Create an audit log entry.
    
    Args:
        actor: User instance or None (for system actions)
        action: Action type (from AuditLog.ACTION_TYPES)
        action_description: Human-readable description
        entity: Model instance being acted upon (optional)
        metadata: Additional context data (dict)
        request: Django request object (optional, for IP/user agent)
    """
    try:
        # Determine actor type
        if actor is None:
            actor_type = 'SYSTEM'
        elif actor.is_superuser or actor.is_staff:
            actor_type = 'ADMIN'
        else:
            actor_type = 'USER'
        
        # Get entity type and ID if entity provided
        entity_type = None
        entity_id = None
        if entity:
            entity_type = ContentType.objects.get_for_model(entity)
            entity_id = entity.pk
        
        # Extract request context if available
        ip_address = None
        user_agent = ''
        request_path = ''
        
        if request:
            # Try to get from request._audit_context (set by middleware)
            audit_context = getattr(request, '_audit_context', {})
            ip_address = audit_context.get('ip_address')
            user_agent = audit_context.get('user_agent', '')
            request_path = audit_context.get('request_path', '')
        
        # Create audit log entry
        AuditLog.objects.create(
            actor=actor,
            actor_type=actor_type,
            action=action,
            action_description=action_description,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent,
            request_path=request_path
        )
        
    except Exception as e:
        # Log error but don't fail the main operation
        # Use print for critical audit logging failures
        import logging
        logger = logging.getLogger('posb_recruitment')
        logger.error(f'Failed to create audit log: {str(e)}')
