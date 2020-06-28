from django.core.exceptions import (
    ImproperlyConfigured,
    PermissionDenied,
    SuspiciousOperation,
)

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
            raise ImproperlyConfigured(
                f"permission {self.permission_name} " "does not exist"
            )


class QuerySetPermissionMixin(BasePermissionMixin):
    """View mixin that filters QuerySets according to a permission.

    Use this mixin with any class-based view that expects a
    ``get_queryset`` method (e.g.
    :class:`~django.views.generic.list.ListView`,
    :class:`~django.views.generic.detail.DetailView`,
    :class:`~django.views.generic.edit.UpdateView`, or any other views
    that subclass from
    :class:`~django.views.generic.list.MultipleObjectMixin` or
    :class:`~django.views.generic.detail.SingleObjectMixin`), and
    supply a :attr:`permission_name` attribute with the name of a
    Bridgekeeper permission.

    The view's queryset will then be automatically filtered to objects
    that the user requesting the page has the supplied permission for.
    For multiple-object views like
    :class:`~django.views.generic.list.ListView`, objects the user
    doesn't have the permission for just won't be in the list.
    For single-object views like
    :class:`~django.views.generic.edit.UpdateView`, attempts to access
    objects the user doesn't have the permission for will just 404.

    .. attribute:: permission_name

        The name of the Bridgekeeper permission to check against, e.g.
        ``'shrubberies.change_shrubbery'``.
    """

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        return self.rule.filter(self.request.user, qs)


class CreatePermissionGuardMixin(BasePermissionMixin):
    """A view that checks permissions before creating model instances.

    Use this mixin with :class:`~django.views.generic.edit.CreateView`,
    and supply the :attr:`permission_name` of a Bridgekeeper permission.
    Your view will then do two things:

    - Check that it's possible for a user to create any new instances
      at all (i.e. that
      :meth:`~bridgekeeper.rules.Rule.is_possible_for` returns ``True``
      on the supplied permission). If not, the mixin raises
      :class:`~django.core.exceptions.PermissionDenied`.
    - Just before the form is saved, checks the unsaved model instance
      against the supplied permission; if it fails, the mixin raises
      :class:`~django.core.exceptions.SuspiciousOperation`.

    Note that unlike :class:`QuerySetPermissionMixin`, this mixin won't
    automatically apply permissions for you. Ideally, your view (or
    the form class your view uses) should make it impossible for
    users to create instances they're not allowed to create; fields
    that must be set to a certain value should be set automatically and
    not displayed in the form, choice fields should have their
    ``choices`` limited to only values the user is allowed to set, and
    so on.

    Bridgekeeper can't (and arguably shouldn't) reach into your form
    and modify it for you. Instead, this mixin provides a last line of
    defence; if your view has a bug where a user can create something
    they're not allowed to, the mixin will prevent the object from
    actually being created, and crash loudly in a way that your error
    reporting systems can pick up, allowing you to fix the bug.

    .. attribute:: permission_name

        The name of the Bridgekeeper permission to check against, e.g.
        ``'shrubberies.change_shrubbery'``.
    """

    def dispatch(self, request, *args, **kwargs):
        if not self.rule.is_possible_for(self.request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if not self.rule.check(self.request.user, form.instance):
            raise SuspiciousOperation(
                "Tried to create an instance which " "permissions do not allow"
            )
        return super().form_valid(form)
