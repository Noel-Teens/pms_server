from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    """
    Custom permission to only allow admin users to access the view.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'ADMIN'

class IsNotFrozen(BasePermission):
    """
    Custom permission to prevent frozen accounts from accessing views.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.status != 'FROZEN'