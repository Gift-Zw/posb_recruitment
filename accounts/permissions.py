"""
Custom permissions for accounts app.
"""
from rest_framework import permissions


class IsHRStaff(permissions.BasePermission):
    """Permission check for employees only."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_employee()


class IsVerifiedUser(permissions.BasePermission):
    """Permission check for verified users only."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_verified
