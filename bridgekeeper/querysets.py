from django.db.models import Manager, QuerySet

from . import perms as global_permission_map


class PermissionQuerySet(QuerySet):
    """A QuerySet subclass that provides a convenience method."""

    __permission_map = global_permission_map

    def visible_to(self, user, permission):
        """Filter the QuerySet to objects a user has a permission for.

        :param user: User to check permission against.
        :type user: django.contrib.auth.models.User
        :param permission: Permission to check.
        :type permission: str

        This method only works with permissions that are defined in
        :data:`~bridgekeeper.perms`;
        regular Django row-level permission checkers can't be invoked on
        the QuerySet level.

        It is a convenience wrapper around
        :meth:`~bridgekeeper.rules.Rule.filter`.
        """

        try:
            rule = self.__permission_map[permission]
        except KeyError:
            raise ValueError(
                "Permission {} does not exist, or is not "
                "registered in Bridgekeeper".format(permission)
            )
        return rule.filter(user, self)


#: Django model manager using :class:`PermissionQuerySet`.
#:
#: For easy access to :class:`PermissionQuerySet` on your models,
#: assign this manager to the ``objects`` property::
#:
#:     class MyModel(models.Model):
#:         ...  # your fields here
#:
#:         objects = PermissionManager()
PermissionManager = Manager.from_queryset(
    PermissionQuerySet, class_name="PermissionManager"
)
