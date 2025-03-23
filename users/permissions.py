from rest_framework.permissions import BasePermission
from .models import ROLES


class IsAdmin(BasePermission):
    """
    Allows access only to admin users.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == ROLES.Admin
        )


# class IsCreator(BasePermission):
#     """
#     Allows access only to creator users.
#     """
#     def has_permission(self, request, view):
#         return request.user and request.user.is_authenticated and request.user.role == ROLES.Creator


class IsResourceOwner(BasePermission):
    """
    Allows access only to the owner of a resource.
    This permission must be used with views that provide an obj with an 'owner' or 'uploader' attribute.
    """

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, "author"):
            return obj.author == request.user
        if hasattr(obj, "uploader"):
            return obj.uploader == request.user
        if hasattr(obj, "user"):
            return obj.user == request.user
        if hasattr(obj, "created_by"):
            return obj.created_by == request.user
        if hasattr(obj, "owner"):
            return obj.owner == request.user
        return False


class IsAdminOrResourceOwner(BasePermission):
    """
    Allows access to admin users or the owner of a resource.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.role == ROLES.Admin:
            return True

        # Check ownership
        if hasattr(obj, "author"):
            return obj.author == request.user
        if hasattr(obj, "uploader"):
            return obj.uploader == request.user
        if hasattr(obj, "user"):
            return obj.user == request.user
        if hasattr(obj, "created_by"):
            return obj.created_by == request.user
        if hasattr(obj, "owner"):
            return obj.owner == request.user
        return False
