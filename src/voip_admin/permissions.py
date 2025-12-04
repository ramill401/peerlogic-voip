"""
Custom permissions for VoIP Admin RBAC."""

from rest_framework import permissions
from src.voip_admin.models import Practice, ProviderConnection


class IsPracticeMember(permissions.BasePermission):
    """
    Permission to check if user belongs to a practice.
    For MVP, we'll use a simple approach: check if user has a practice attribute.
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check if user has access to this practice."""
        # If object is a Practice, check membership
        if isinstance(obj, Practice):
            return self._user_has_practice_access(request.user, obj)
        
        # If object has a practice attribute, check that
        if hasattr(obj, 'practice'):
            return self._user_has_practice_access(request.user, obj.practice)
        
        # If object is a ProviderConnection, check its practice
        if isinstance(obj, ProviderConnection):
            return self._user_has_practice_access(request.user, obj.practice)
        
        return False
    
    def _user_has_practice_access(self, user, practice):
        """
        Check if user has access to a practice.
        
        For MVP: Superusers have access to all practices.
        Regular users need to be associated with the practice.
        
        TODO: Implement proper user-practice association model.
        For now, superusers can access everything.
        """
        if user.is_superuser:
            return True
        
        # TODO: Add user.practice relationship check when user-practice model exists
        # For now, allow authenticated users (will be restricted by practice filtering)
        return True


class CanManageVoIP(permissions.BasePermission):
    """
    Permission to manage VoIP resources.
    Requires user to be admin or have VoIP management permissions.
    """
    
    def has_permission(self, request, view):
        """Check if user can manage VoIP."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusers can do everything
        if request.user.is_superuser:
            return True
        
        # Check if user is in 'voip_admin' group or has specific permission
        # For MVP, allow all authenticated users
        # TODO: Implement proper group-based permissions
        return True


class CanAccessConnection(permissions.BasePermission):
    """
    Permission to access a specific provider connection.
    Checks practice-level access.
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user can access this connection."""
        if not isinstance(obj, ProviderConnection):
            return False
        
        # Superusers can access everything
        if request.user.is_superuser:
            return True
        
        # Check practice access
        return IsPracticeMember()._user_has_practice_access(request.user, obj.practice)

