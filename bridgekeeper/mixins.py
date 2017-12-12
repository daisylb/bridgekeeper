from django.core.exceptions import (ImproperlyConfigured, PermissionDenied,
                                    SuspiciousOperation)

from . import perms as global_permission_map


class BasePermissionMixin:
    def __init__(self, permission_map=None, *args, **kwargs):
        if permission_map is None:
            permission_map = global_permission_map
        try:
            self.rule = permission_map[self.permission_name]
        except AttributeError:
            raise ImproperlyConfigured("permission_name is not set")
        except KeyError:
            raise ImproperlyConfigured(f"permission {self.permission_name} "
                                       "does not exist")


class QuerySetPermissionMixin(BasePermissionMixin):
    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        return self.rule.filter(self.request.user, qs)


class CreatePermissionGuardMixin(BasePermissionMixin):
    def dispatch(self, request, *args, **kwargs):
        if not self.rule.is_possible_for(self.request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if not self.rule.check(self.request.user, form.instance):
            raise SuspiciousOperation("Tried to create an instance which "
                                      "permissions do not allow")
        return super().form_valid(form)
