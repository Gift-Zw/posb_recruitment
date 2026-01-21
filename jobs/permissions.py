"""
Custom permissions for jobs app.
"""
from rest_framework import permissions


class IsHRStaffOrReadOnly(permissions.BasePermission):
    """Allow read-only access to everyone, write access to employees only."""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated and request.user.is_employee()
