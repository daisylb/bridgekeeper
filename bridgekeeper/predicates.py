"""Predicate library that forms the core of Bridgekeeper.

This module defines the :class:`Predicate` base class, as well as a
number of built-in predicates.
"""

from django.db.models import Q


class Sentinel:
    def __init__(self, name):
        self.repr = name

    def __repr__(self):
        return self.repr


#: A sentinel value that represents the universal set. See
#: :meth:`Predicate.query` for usage.
UNIVERSAL = Sentinel("UNIVERSAL")

#: A sentinel value that represents the empty set. See
#: :meth:`Predicate.query` for usage.
EMPTY = Sentinel("EMPTY")


class Predicate:
    """Base class for predicates.

    All predicates are instances of this class, but not directly;
    use (or write!) a subclass instead, as this class will raise
    :class:`NotImplementedError` if you try to actually do anything
    with it.

    Subclasses will need to override the :meth:`query` and :meth:`check`
    methods.

    .. note::

        To aid in testing, here are some invariants that every instance
        of every subclass of this class should satisfy:

        - For every user ``u``, for every instance ``i`` of a given
          model ``A``, ``check(u, i)`` should be ``True`` if and only if
          ``u`` is in the queryset returned by
          ``filter(u, A.objects.all())``
        - For every user ``u``, for every queryset ``q``:

            - ``filter(u, q)`` returns ``UNIVERSAL`` if and only if
              ``check(u, i)`` returns ``True`` for every possible
              instance ``i``.
            - ``filter(u, q)`` returns ``EMPTY`` if and only if
              ``check(u, i)`` returns ``False`` for every possible
              instance ``i``.
            - ``check(u, None)`` returns ``True`` if and only if
              ``filter(u, q)`` returns ``UNIVERSAL``.
    """

    def filter(self, user, queryset):
        """Filter a queryset to instances that satisfy this predicate.

        Given a queryset and a user, this method will return a filtered
        queryset that contains only instances from the original
        queryset for which the user satisfies this predicate.

        :param queryset: The initial queryset to filter
        :type queryset: django.db.models.QuerySet
        :param user: The user to match against.
        :type user: django.contrib.auth.models.User
        :returns: A filtered queryset
        :rtype: django.db.models.QuerySet

        .. warning::

            If you are subclassing this class, don't override this
            method; override :meth:`query` instead.
        """
        q_obj = self.query(user)
        if q_obj is UNIVERSAL:
            return queryset
        if q_obj is EMPTY:
            return queryset.none()
        return queryset.filter(q_obj)

    def is_possible_for(self, user):
        """Check if it is possible for a user to satisfy this predicate.

        Returns ``True`` if it is possible for an instance to exist for
        which the given user satisfies this predicate, ``False``
        otherwise.

        For example, in a multi-tenanted app, you might have a predicate
        that allows access to model instances if a user is a staff user,
        or if the instance's tenant matches the user's tenant.

        In that case, :meth:`check`, when called without an instance,
        would return ``True`` only for staff users (since only they can
        see *every* instance). This method would return ``True`` for all
        users, because every user could possibly see an instance
        (whether it's one that exists currently in the database, or a
        hypothetical one that might in the future).

        Cases where this method would return ``False`` include where a
        user doesn't have the right role or subscription plan to use a
        feature at all; this method is the single-permission equivalent
        of :ref:`has-module-perms`.
        """
        return self.query(user) is not EMPTY

    def query(self, user):
        """Generate a :class:`~django.db.models.Q` object.

        .. note::

            This method is used internally by :meth:`filter`; subclasses
            will need to override it but you should never need to call
            it directly.

        Given a user, return a :class:`~django.db.models.Q` object which
        will filter a queryset down to only instances for which the
        given user satisfies this predicate.

        Alternatively, return :data:`UNIVERSAL` if this user satisfies
        this predicate for every possible object, or :data:`EMPTY` if
        this user cannot satisfy this predicate for any possible object.
        (These two values are usually only returned in "ambient
        predicates" which depend only on some property of the user, e.g.
        the built-in :any:`is_staff`, but these are usually best created
        with the :class:`ambient` decorator.)

        :param user: The user to match against.
        :type user: django.contrib.auth.models.User
        :returns: A query that will filter a queryset to match this
            predicate.
        :rtype: django.db.models.Q
        """
        raise NotImplementedError()

    def check(self, user, instance=None):
        """Check if a user satisfies this predicate.

        Given a user, return a boolean indicating if that user satisfies
        this predicate for a given instance, or if none is provided,
        every instance.
        """
        raise NotImplementedError()

    def __and__(self, other):
        return And(self, other)

    def __or__(self, other):
        return Or(self, other)

    def __not__(self):
        return Not(self)


class BinaryCompositePredicate(Predicate):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return "({!r} {} {!r})".format(self.left, self.sym, self.right)


class And(BinaryCompositePredicate):
    sym = "&"

    def query(self, user):
        # Effectively an intersection (∩) of the two sets represented by
        # left and right's Q expressions, but wth special-casing for the
        # EMPTY (∅) and UNIVERSAL (U) values.
        left = self.left.query(user)
        # Because A ∩ ∅ = ∅, if either side returns EMPTY the entire
        # expression is EMPTY.
        if left is EMPTY:
            # Short-circuit evaluation, since the result of the RHS
            # can't affect what we'll return here
            return EMPTY
        right = self.right.query(user)
        if right is EMPTY:
            return EMPTY
        # Because A ∩ U = A, if one side returns UNIVERSAL the entire
        # expression is whatever is on the other side.
        if left is UNIVERSAL:
            return right
        if right is UNIVERSAL:
            return left
        return left & right

    def check(self, user, instance=None):
        return (self.left.check(user, instance) and
                self.right.check(user, instance))


class Or(BinaryCompositePredicate):
    sym = "|"

    def query(self, user):
        # Effectively a union (∪) of the two sets represented by left
        # and right's Q expressions, but wth special-casing for the
        # EMPTY (∅) and UNIVERSAL (U) values.
        left = self.left.query(user)
        # Because A ∪ U = U, if either side returns UNIVERSAL the entire
        # expression is UNIVERSAL.
        if left is UNIVERSAL:
            # Short-circuit evaluation, since the result of the RHS
            # can't affect what we'll return here
            return UNIVERSAL
        right = self.right.query(user)
        if right is UNIVERSAL:
            return UNIVERSAL
        # Because A ∪ ∅ = A, if one side returns EMPTY the entire
        # expression is whatever is on the other side.
        if left is EMPTY:
            return right
        if right is EMPTY:
            return left
        return left | right

    def check(self, user, instance=None):
        return (self.left.check(user, instance) or
                self.right.check(user, instance))


class Not(Predicate):
    def __init__(self, base):
        self.base = base

    def __repr__(self):
        return "~{!r}".format(self.base)

    def query(self, user):
        base = self.base.query(user)
        # Special case EMPTY and UNIVERSAL by inverting them.
        if base is EMPTY:
            return UNIVERSAL
        if base is UNIVERSAL:
            return EMPTY
        return ~base

    def check(self, user, instance=None):
        return not self.base.check(user, instance)


class ambient(Predicate):  # noqa: used as a decorator, so should be lowercase
    """A decorator for predicates that don't depend on objects.

    This decorator provides a shorthand method for defining predicates
    that depend only on the user. Decorate a function that takes a
    :class:`~django.contrib.auth.models.User` object and returns a
    boolean, and it will be turned into a :class:`Predicate` instance,
    for example::

        @ambient
        def is_anonymous(user):
            return user.is_anonymous
    """

    def __init__(self, predicate_func, repr_string=None):
        self.predicate_func = predicate_func
        self.repr = repr_string or predicate_func.__name__

    def __repr__(self):
        return self.repr

    def query(self, user):
        return UNIVERSAL if self.predicate_func(user) else EMPTY

    def check(self, user, instance=None):
        return self.predicate_func(user)


@ambient
def always_allow(_):
    return True


@ambient
def always_deny(_):
    return False


@ambient
def is_authenticated(user):
    return user.is_authenticated()


@ambient
def is_superuser(user):
    return user.is_superuser


@ambient
def is_staff(user):
    return user.is_staff


@ambient
def is_active(user):
    return user.is_active()


class Attribute(Predicate):
    """Predicate class that checks the value of an instance attribute.

    This predicate is satisfied by model instances where the attribute
    given in ``attr`` matches the value given in ``matches``.

    :param attr: An attribute name to match against on the
        model instance.
    :type attr: str
    :param value: The value to match against, or a callable that takes
        a user and returns a value to match against.

    For instance, if you had a model class ``Widget`` with an attribute
    ``colour`` that was either ``'red'``, ``'green'`` or ``'blue'``,
    you could limit access to blue widgets with the following::

        blue_widgets_only = Attribute('colour', matches='blue')

    Restricting access in a multi-tenanted application by matching a
    model's ``tenant`` to the user's might look like this::

        applications_by_tenant = Attribute('tenant',
                                           lambda user: user.tenant)

    .. warning::

        This predicate uses Python equality (``==``) when checking a
        retrieved Python object, but performs an equality check on the
        database when filtering a QuerySet. Avoid using it with
        imprecise types (e.g. floats), and ensure that you are using the
        correct Python type (e.g. :class:`decimal.Decimal` for decimals
        rather than floats or strings), to prevent inconsistencies.
    """

    def __init__(self, attr, matches):
        self.attr = attr
        self.matches = matches

    def get_match(self, user):
        return self.matches(user) if callable(self.matches) else self.matches

    def __repr__(self):
        return "Attribute({!r}, matches={!r})".format(self.attr, self.matches)

    def query(self, user):
        return Q(**{self.attr: self.get_match(user)})

    def check(self, user, instance=None):
        if instance is None:
            return False
        return getattr(instance, self.attr) == self.get_match(user)


class Is(Predicate):
    """Predicate class that checks the identity of the instance.

    This predicate is satisfied only by the specific model instance that
    is passed in as an argument.

    :param instance: The instance to match against, or a callable that
        takes a user and returns a value to match against.

    For instance, if you only wanted a user to be able to update their
    own profile::

        own_profile = Is(lambda user: user.profile)
    """

    def __init__(self, instance):
        self.instance = instance

    def get_instance(self, user):
        return self.instance(user) if callable(self.instance) else self.instance

    def __repr__(self):
        return "Is({!r})".format(self.instance)

    def query(self, user):
        return Q(pk=self.get_instance(user).pk)

    def check(self, user, instance=None):
        if instance is None:
            return False
        return instance == self.get_instance(user)


class Relation(Predicate):
    """Check that a predicate applies to a ForeignKey.

    :param attr: Name of a foreign key attribute to check.
    :type attr: str
    :param model: Model class on the other side of the foreign key.
    :type model: type
    :param predicate: Predicate to check the foreign key against.
    :type predicate: Predicate

    For example, given ``Applicant`` and ``Application`` models,
    to allow access to all applications to anyone who has permission to
    access the related applicant::

        perms['foo.view_application'] = Relation(
            'applicant', Applicant, perms['foo.view_applicant'])
    """

    def __init__(self, attr, model, predicate):
        self.attr = attr
        self.model = model
        self.predicate = predicate

    def __repr__(self):
        return "Relation({!r}, {}, {!r})".format(
            self.attr, self.model.__name__, self.predicate)

    def query(self, user):
        # Unfortunately you can't use Q objects on a relation, only proper
        # QuerySets.
        related_q = self.predicate.query(user)
        if related_q is UNIVERSAL or related_q is EMPTY:
            return related_q
        return Q(**{self.attr + '__in': self.model.objects.filter(related_q)})

    def check(self, user, instance=None):
        if instance is None:
            return self.predicate.check(user, None)
        return self.predicate.check(user, getattr(instance, self.attr))


class ManyRelation(Predicate):
    """Check that a predicate applies to a many-object relationship.

    This can be used in a similar fashion to :class:`Relation`, but
    across a :class:`~django.db.models.ManyToManyField`, or the remote
    end of a :class:`~django.db.models.ForeignKey`.

    :param attr: Name of a many-object relationship to check. This is
        the accessor name; the name that you access on a model
        instance to get a manager for the other side of the
        relationship. If you are on the reverse side of the relationship
        (the side where the field is *not* defined), this is typically
        ``mymodel_set``, where ``mymodel`` is the lowercased model name,
        unless you've set
        :attr:`~django.db.models.ForeignKey.related_name`.
    :type attr: str
    :param query_attr: Query name to use; that is, the name that you
        use when filtering this relationship using ``.filter()``.
        If you are on the side of the relationship where the field
        is defined, this is typically the lowercased model name (e.g.
        ``mymodel`` on its own, *not* ``mymodel_set``), unless you've
        set :attr:`~django.db.models.ForeignKey.related_name` or
        :attr:`~django.db.models.ForeignKey.related_query_name`.
    :type query_attr: str
    :param model: Model class on the other side of the relationship.
    :type model: type
    :param predicate: Predicate to check the foreign object against.
    :type predicate: Predicate

    For example, given ``Agency`` and ``Customer`` models,
    to allow agency users access only to customers that have a
    relationship with their agency::

        perms['foo.view_customer'] = ManyRelation(
            'agencies', Agency, Is(lambda user: user.agency))
    """

    def __init__(self, attr, query_attr, model, predicate):
        # TODO: add support for 'all' as well as 'exists'
        self.attr = attr
        self.query_attr = query_attr
        self.model = model
        self.predicate = predicate

    def __repr__(self):
        return "ManyRelation({!r}, {}, {}, {!r})".format(
            self.attr, self.query_attr, self.model.__name__, self.predicate)

    def query(self, user):
        # Unfortunately you can't use Q objects on a relation, only proper
        # QuerySets.
        related_q = self.predicate.query(user)
        if related_q is UNIVERSAL or related_q is EMPTY:
            return related_q
        return Q(**{self.query_attr + '__in': self.model.objects.filter(related_q)})

    def check(self, user, instance=None):
        if instance is None:
            return self.predicate.check(user, None)
        related_q = self.predicate.query(user)
        if related_q is UNIVERSAL or related_q is EMPTY:
            return related_q
        related_manager = getattr(instance, self.attr)
        return related_manager.filter(related_q).exists()
