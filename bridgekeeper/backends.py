from . import perms as global_permission_map


class RulePermissionBackend:
    # Because Django calls out to authentication backends when consumers
    # call .has_perm() and friends on a User, we need to provide one.
    # Fortunately, Django consults every authentication backend, not
    # just the one the user logged in with.

    def __init__(self, permission_map=None):
        if permission_map is None:
            permission_map = global_permission_map
        self.permission_map = permission_map

    def authenticate(self, **kwargs):
        # We don't actually want to handle authentication in
        # this backend.
        pass

    def has_perm(self, user, perm, obj=None):
        try:
            return self.permission_map[perm].check(user, obj)
        except KeyError:
            return False

    def has_perms(self, user, perms, obj=None):
        for perm in perms:
            if not self.has_perm(user, perm, obj):
                return False
        return True

    def has_module_perms(self, user, app_label):
        prefix = "{}.".format(app_label)
        for label, rule in self.permission_map.items():
            if not label.startswith(prefix):
                continue
            if rule.is_possible_for(user):
                return True
        return False
