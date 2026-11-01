from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwnerOrReadOnly(BasePermission):
    owner_field = None
    message = "You do not have permission to modify this object."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        return getattr(obj, f"{self.owner_field}_id") == request.user.pk


class IsRoomHostOrReadOnly(IsOwnerOrReadOnly):
    owner_field = "host"
    message = "Only the room host may modify this room."


class IsMessageAuthorOrReadOnly(IsOwnerOrReadOnly):
    owner_field = "user"
    message = "Only the message author may modify this message."
