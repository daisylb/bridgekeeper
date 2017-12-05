from django.core.exceptions import (ImproperlyConfigured, PermissionDenied,
                                    SuspiciousOperation)

from .registry import registry as global_registry


class BasePermissionMixin:
    def __init__(self, registry=None, *args, **kwargs):
        if registry is None:
            registry = global_registry
        try:
            self.predicate = registry[self.permission_name]
        except AttributeError:
            raise ImproperlyConfigured("permission_name is not set")
        except KeyError:
            raise ImproperlyConfigured(f"permission {self.permission_name} "
                                       "does not exist")


class QuerySetPermissionMixin(BasePermissionMixin):
    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        return self.predicate.filter(qs, self.request.user)


class CreatePermissionGuardMixin(BasePermissionMixin):
    def dispatch(self, request, *args, **kwargs):
        if not self.predicate.is_possible_for(self.request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if not self.predicate.apply(self.request.user, form.instance):
            raise SuspiciousOperation("Tried to create an instance which "
                                      "permissions do not allow")
        return super().form_valid(form)
