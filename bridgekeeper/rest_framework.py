from logging import getLogger

from bridgekeeper import perms
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model, QuerySet
from rest_framework.filters import BaseFilterBackend
from rest_framework.permissions import BasePermission

logger = getLogger(__name__)


class BridgekeeperRESTMixin:
    """Mixin for Django REST Framework integration classes."""

    def skip_permission_checks(self, request, view, obj=None):
        """Skips all permission checks for certain requests.

        The default implementation will skip permission checks for
        the ``APIRootView`` view class used by the built-in
        ``DefaultRouter``.

        :returns: Whether to skip permission checks for the
            given request.
        :rtype: bool
        """
        # This causes an import cycle if it's at the top level,
        # because REST Framework has import side effects, yay
        from rest_framework.routers import APIRootView

        if isinstance(view, APIRootView):
            return True
        return False

    def get_action(self, request, view, obj=None):
        """Return the action that a particular request is performing.

        Usually, this is one of ``'view'``, ``'add'``, ``'change'``
        or ``'delete'``. This is used by :meth:`get_permission_name`
        to generate the name of the appropriate permission.

        :returns: Name of an action.
        :rtype: str
        """
        if request.method in ("GET", "OPTIONS", "HEAD"):
            return "view"
        if request.method == "POST":
            return "add"
        if request.method in ("PUT", "PATCH"):
            return "change"
        if request.method == "DELETE":
            return "delete"
        raise ValueError(
            "{method} isn't a HTTP method that "
            "RulePermissions knows about, so it's unable to "
            "determine the correct permission name for this "
            "request. Subclass RulePermissions and override "
            "get_action or get_permission_name to provide the "
            "correct permission name for requests like this.".format(
                method=request.method
            )
        )

    def get_operand_name(self, request, view, obj=None):
        """Return the name of the thing that a request is acting on.

        The default implementation works if ``obj`` is a model instance
        (when it is provided), or if ``view`` is a view that has either
        a ``queryset`` attribute or ``get_queryset()`` method
        (otherwise).

        This is used by :meth:`get_permission_name` to generate the name
        of the appropriate permission.

        :returns: A tuple in the form (app_label, operand_name).
        :rtype: (str, str)
        """
        if isinstance(obj, Model):
            model = obj.__class__
        elif obj is not None:
            raise TypeError(
                "{obj!r} is not a model instance, so "
                "RulePermissions is incapable of determining "
                "the correct permission name for it. Subclass "
                "RulePermissions and override get_operand_name "
                "or get_permission_name to provide the correct "
                "permission name for objects of this type.".format(obj=obj)
            )
        elif hasattr(view, "get_queryset") and callable(view.get_queryset):
            model = view.get_queryset().model
        elif hasattr(view, "queryset") and isinstance(view.queryset, QuerySet):
            model = view.queryset.model
        else:
            raise ValueError(
                "{view!r} does not provide a 'queryset' "
                "attribute or a 'get_queryset()' method, so "
                "RulePermissions is incapable of determining "
                "the correct permission name for it. Subclass "
                "RulePermissions and override get_operand_name "
                "or get_permission_name to provide the correct "
                "permission name for views like this.".format(view=view)
            )

        return (model._meta.app_label, model._meta.model_name)

    def get_permission_name(self, request, view, obj=None):
        """Return the name of the permission to use for a request.

        The default implementation returns a name of the form
        ``'{app_label}.{action}_{operand_name}'``, which will result in
        something like ``'shrubberies.view_shrubber'`` or
        ``'shrubberies.delete_shrubbery'``.

        ``app_label`` and ``operand_name`` are provided by
        :meth:`get_operand_name`, and ``action`` is provided by
        :meth:`get_action`, so if you need to override this behaviour,
        it may be easier to override those methods instead.

        :returns: Permission name.
        :rtype: str
        """
        action = self.get_action(request, view, obj)
        app_label, operand_name = self.get_operand_name(request, view, obj)
        return "{app_label}.{action}_{operand_name}".format(
            action=action, app_label=app_label, operand_name=operand_name
        )

    def get_permission(self, request, view, obj=None):
        """Return a rule object to check against for this request.

        The default implementation just looks up the name returned by
        :meth:`get_permission_name`.

        :returns: Rule object.
        :rtype: bridgekeeper.rules.Rule
        """
        name = self.get_permission_name(request, view, obj)
        print(name, flush=True)
        try:
            return perms[name]
        except KeyError:
            raise ImproperlyConfigured(
                "A permission named {name} could not be found in the "
                "Bridgekeeper permission registry. Define a permission "
                "with that name, or subclass RulePermissions and "
                "override get_permission or get_permission_name "
                "to return the correct permission.".format(name=name)
            )


class RulePermissions(BridgekeeperRESTMixin, BasePermission):
    """Django REST Framework permission class for Bridgekeeper.

    Note that this class **does not**, by itself, perform queryset
    filtering on list views, since Django REST Framework doesn't provide
    an API for permission classes to do so.
    """

    def has_permission(self, request, view):
        if self.skip_permission_checks(request, view):
            return True
        return self.get_permission(request, view).is_possible_for(request.user)

    def has_object_permission(self, request, view, obj):
        if self.skip_permission_checks(request, view, obj):
            return True
        return self.get_permission(request, view, obj).check(request.user, obj)


class RuleFilter(BridgekeeperRESTMixin, BaseFilterBackend):
    """Django REST Framework filter class for Bridgekeeper.

    This filter class doesn't expect any client interaction or present
    any UI to the API explorer; it's simply a mechanism for
    automatically filtering QuerySets according to Bridgekeeper
    permissions.

    Note that this filter will always check the ``view`` permission;
    this means that if a particular user has permissions to edit but not
    view something, they'll get 404s on everything. That said, it
    doesn't make much sense for users to have edit but not view
    permissions on something anyway.
    """

    def get_action(self, request, view, obj=None):
        return "view"

    def filter_queryset(self, request, queryset, view):
        if self.skip_permission_checks(request, view):
            return queryset
        return self.get_permission(request, view).filter(request.user, queryset)
