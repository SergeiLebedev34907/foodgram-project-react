from rest_framework.permissions import BasePermission, SAFE_METHODS


class PersonalPermission(BasePermission):
    def has_permission(self, request, view):
        path = request._request.path
        user_is_auth = request.user.is_authenticated
        if path == '/api/users/me/' and not user_is_auth:
            return False
        return super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or request.user.is_staff
