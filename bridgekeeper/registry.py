from .predicates import EMPTY


class Registry(dict):
    def __setitem__(self, key, value):
        if key in self:
            raise ValueError("The permission already exists", value)
        super().__setitem__(key, value)


registry = Registry()


class RulePermissionBackend:
    # Because Django calls out to authentication backends when consumers
    # call .has_perm() and friends on a User, we need to provide one.
    # Fortunately, Django consults every authentication backend, not
    # just the one the user logged in with.

    def __init__(self, registry=None):
        if registry is None:
            registry = globals()['registry']
        self.registry = registry

    def authenticate(self, **kwargs):
        # We don't actually want to handle authentication in
        # this backend.
        pass

    def has_perm(self, user, perm, obj=None):
        try:
            return self.registry[perm].apply(user, obj)
        except KeyError:
            return False

    def has_perms(self, user, perms, obj=None):
        for perm in perms:
            if not self.has_perm(user, perm, obj):
                return False
        return True

    def has_module_perms(self, user, app_label):
        prefix = "{}.".format(app_label)
        for label, predicate in self.registry.items():
            if not label.startswith(prefix):
                continue
            if predicate.query(user) is not EMPTY:
                return True
        return False
