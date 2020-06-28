"""Rule library that forms the core of Bridgekeeper.

This module defines the :class:`Rule` base class, as well as a
number of built-in rules.
"""

from django.db.models import Manager, Q, QuerySet
from django.db.models.fields.reverse_related import ForeignObjectRel


class Sentinel:
    def __init__(self, name):
        self.repr = name

    def __repr__(self):
        return self.repr


#: A sentinel value that represents the universal set. See
#: :meth:`Rule.query` for usage.
UNIVERSAL = Sentinel("UNIVERSAL")

#: A sentinel value that represents the empty set. See
#: :meth:`Rule.query` for usage.
EMPTY = Sentinel("EMPTY")


class Rule:
    """Base class for rules.

    All rules are instances of this class, but not directly;
    use (or write!) a subclass instead, as this class will raise
    :class:`NotImplementedError` if you try to actually do anything
    with it.
    """

    def filter(self, user, queryset):
        """Filter a queryset to instances that satisfy this rule.

        Given a queryset and a user, this method will return a filtered
        queryset that contains only instances from the original
        queryset for which the user satisfies this rule.

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
        """Check if it is possible for a user to satisfy this rule.

        Returns ``True`` if it is possible for an instance to exist for
        which the given user satisfies this rule, ``False``
        otherwise.

        For example, in a multi-tenanted app, you might have a rule
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
        given user satisfies this rule.

        Alternatively, return :data:`UNIVERSAL` if this user satisfies
        this rule for every possible object, or :data:`EMPTY` if
        this user cannot satisfy this rule for any possible object.
        (These two values are usually only returned in "blanket
        rules" which depend only on some property of the user, e.g.
        the built-in :any:`is_staff`, but these are usually best created
        with the :class:`blanket_rule` decorator.)

        :param user: The user to match against.
        :type user: django.contrib.auth.models.User
        :returns: A query that will filter a queryset to match this
            rule.
        :rtype: django.db.models.Q
        """
        raise NotImplementedError()

    def check(self, user, instance=None):
        """Check if a user satisfies this rule.

        Given a user, return a boolean indicating if that user satisfies
        this rule for a given instance, or if none is provided,
        every instance.
        """
        raise NotImplementedError()

    def __and__(self, other):
        return And(self, other)

    def __or__(self, other):
        return Or(self, other)

    def __not__(self):
        return Not(self)

    def __invert__(self):
        return Not(self)


class BinaryCompositeRule(Rule):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return "({!r} {} {!r})".format(self.left, self.sym, self.right)


class And(BinaryCompositeRule):
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
        return self.left.check(user, instance) and self.right.check(user, instance)


class Or(BinaryCompositeRule):
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
        return self.left.check(user, instance) or self.right.check(user, instance)


class Not(Rule):
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

    def __invert__(self):
        return self.base


class blanket_rule(Rule):  # noqa: used as a decorator, so should be lowercase
    """A decorator for rules that don't depend on objects.

    This decorator provides a shorthand method for defining rules
    that depend only on the user. Decorate a function that takes a
    :class:`~django.contrib.auth.models.User` object and returns a
    boolean, and it will be turned into a :class:`Rule` instance,
    for example::

        @blanket_rule
        def is_anonymous(user):
            return user.is_anonymous
    """

    def __init__(self, rule_func, repr_string=None):
        self.rule_func = rule_func
        self.repr = repr_string or rule_func.__name__

    def __repr__(self):
        return self.repr

    def query(self, user):
        return UNIVERSAL if self.rule_func(user) else EMPTY

    def check(self, user, instance=None):
        return self.rule_func(user)


@blanket_rule
def always_allow(_):
    return True


@blanket_rule
def always_deny(_):
    return False


@blanket_rule
def is_authenticated(user):
    return user.is_authenticated


@blanket_rule
def is_superuser(user):
    return user.is_superuser


@blanket_rule
def is_staff(user):
    return user.is_staff


@blanket_rule
def is_active(user):
    return user.is_active


class R(Rule):
    """Rules that allow access to some objects but not others.

    ``R`` takes a set of field lookups as keyword arguments.

    Each argument is a model attribute. Foreign keys can be traversed
    using double underscores, as in :class:`~django.db.models.Q`
    objects.

    The value assigned to each argument can be:

    - A value to match.
    - A function that accepts a user, and returns a value to match.
    - If the argument refers to a foreign key or many-to-many
      relationship, another :class:`~bridgekeeper.rules.Rule` object.
    """

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __repr__(self):
        return "R({})".format(
            ", ".join("{}={!r}".format(k, v) for k, v in self.kwargs.items())
        )

    def check(self, user, instance=None):
        if instance is None:
            return False

        # This loop exits early, returning False, if any argument
        # doesn't match.
        for key, value in self.kwargs.items():

            # Find the appropriate LHS on this object, traversing
            # foreign keys if necessary.
            lhs = instance
            for key_fragment in key.split("__"):
                field = lhs.__class__._meta.get_field(key_fragment,)
                if isinstance(field, ForeignObjectRel):
                    attr = field.get_accessor_name()
                else:
                    attr = key_fragment
                lhs = getattr(lhs, attr)

            # Compare it against the RHS.
            # Note that the LHS will usually be a value, but in the case
            # of a ManyToMany or the 'other side' of a ForeignKey it
            # will be a RelatedManager. In this case, we need to check
            # if there is at least one model that matches the RHS.
            if isinstance(value, Rule):
                if isinstance(lhs, Manager):
                    if not value.filter(user, lhs.all()).exists():
                        return False
                else:
                    if not value.check(user, lhs):
                        return False
            else:
                resolved_value = value(user) if callable(value) else value
                if isinstance(lhs, Manager):
                    if resolved_value not in lhs.all():
                        return False
                else:
                    if lhs != resolved_value:
                        return False

        # Woohoo, everything matches!
        return True

    def query(self, user):
        accumulated_q = Q()

        for key, value in self.kwargs.items():
            # TODO: check lookups are not being used
            if isinstance(value, Rule):
                child_q_obj = value.query(user)
                accumulated_q &= add_prefix(child_q_obj, key)
            else:
                resolved_value = value(user) if callable(value) else value
                accumulated_q &= Q(**{key: resolved_value})

        return accumulated_q


class Attribute(Rule):
    """Rule class that checks the value of an instance attribute.

    .. deprecated:: 0.9

        Use :class:`~bridgekeeper.rules.R` objects instead.

        ::

            # old
            Attribute('colour', matches='blue')
            Attribute('tenant', lambda user: user.tenant)

            # new
            R(colour='blue')
            R(tenant=lambda user: user.tenant)

    This rule is satisfied by model instances where the attribute
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

        This rule uses Python equality (``==``) when checking a
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


class Is(Rule):
    """Rule class that checks the identity of the instance.

    This rule is satisfied only by a the provided model instance.

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


#: This rule is satisfied by the user object itself.
current_user = Is(lambda user: user)


class In(Rule):
    """Rule class that checks the instance is a member of a collection.

    This rule is satisfied only by model instances that are members of
    the provided collection.

    :param collection: The collection to match against, or a callable
        that takes a user and returns a value to match against.

    For instance, if you only wanted to match groups a user is in::

        own_profile = Is(lambda user: user.profile)
    """

    def __init__(self, collection):
        self.collection = collection

    def get_collection(self, user):
        return self.collection(user) if callable(self.collection) else self.collection

    def __repr__(self):
        return "In({!r})".format(self.collection)

    def query(self, user):
        collection = self.get_collection(user)
        if isinstance(collection, QuerySet):
            return Q(pk__in=collection.values_list("pk"))
        return Q(pk__in=[x.pk for x in collection])

    def check(self, user, instance=None):
        if instance is None:
            return False

        collection = self.get_collection(user)

        if isinstance(collection, QuerySet):
            # If we have a queryset, the rule passes if the instance is
            # of the same model, and the pk is present in the qs
            if not isinstance(instance, collection.model):
                return False
            return collection.filter(pk=instance.pk).exists()

        return instance in collection


#: This rule is satisfied by any group the user is in.
in_current_groups = In(lambda user: user.groups.all())

# from https://groups.google.com/forum/#!msg/django-developers/jEkCdzGnzRE/6lJQV4AqCwAJ


def add_prefix(q_obj, prefix):
    return Q(
        *(
            add_prefix(child, prefix)
            if isinstance(child, Q)
            else (prefix + "__" + child[0], child[1])
            for child in q_obj.children
        ),
        _connector=q_obj.connector,
        _negated=q_obj.negated,
    )


class Relation(Rule):
    """Check that a rule applies to a ForeignKey.

    .. deprecated:: 0.9

        Use :class:`~bridgekeeper.rules.R` objects instead.

        ::

            # old
            Relation('applicant', perms['foo.view_applicant'])

            # new
            R(applicant=perms['foo.view_applicant'])

    :param attr: Name of a foreign key attribute to check.
    :type attr: str
    :param rule: Rule to check the foreign key against.
    :type rule: Rule

    For example, given ``Applicant`` and ``Application`` models,
    to allow access to all applications to anyone who has permission to
    access the related applicant::

        perms['foo.view_application'] = Relation(
            'applicant', perms['foo.view_applicant'])
    """

    def __init__(self, attr, rule):
        self.attr = attr
        self.rule = rule

    def __repr__(self):
        return "Relation({!r}, {!r})".format(self.attr, self.rule)

    def query(self, user):
        related_q = self.rule.query(user)
        if related_q is UNIVERSAL or related_q is EMPTY:
            return related_q
        return add_prefix(related_q, self.attr)

    def check(self, user, instance=None):
        if instance is None:
            return self.rule.check(user, None)
        return self.rule.check(user, getattr(instance, self.attr))


class ManyRelation(Rule):
    """Check that a rule applies to a many-object relationship.

    .. deprecated:: 0.9

        Use :class:`~bridgekeeper.rules.R` objects instead.

        ::

            # old
            ManyRelation('agency', Is(lambda user: user.agency))

            # new
            R(agency=lambda user: user.agency)

    This can be used in a similar fashion to :class:`Relation`, but
    across a :class:`~django.db.models.ManyToManyField`, or the remote
    end of a :class:`~django.db.models.ForeignKey`.

    :param query_attr: Name of a many-object relationship to check. This
        This is the name that you
        use when filtering this relationship using ``.filter()``.
        If you are on the side of the relationship where the field
        is defined, this is typically the lowercased model name (e.g.
        ``mymodel`` on its own, *not* ``mymodel_set``), unless you've
        set :attr:`~django.db.models.ForeignKey.related_name` or
        :attr:`~django.db.models.ForeignKey.related_query_name`.
    :type query_attr: str
    :param rule: Rule to check the foreign object against.
    :type rule: Rule

    For example, given ``Agency`` and ``Customer`` models,
    to allow agency users access only to customers that have a
    relationship with their agency::

        perms['foo.view_customer'] = ManyRelation(
            'agency', Is(lambda user: user.agency))
    """

    def __init__(self, query_attr, rule):
        # TODO: add support for 'all' as well as 'exists'
        self.query_attr = query_attr
        self.rule = rule

    def __repr__(self):
        return "ManyRelation({!r}, {!r})".format(self.query_attr, self.rule)

    def query(self, user):
        # Unfortunately you can't use Q objects on a relation, only proper
        # QuerySets.
        related_q = self.rule.query(user)
        if related_q is UNIVERSAL or related_q is EMPTY:
            return related_q
        return add_prefix(related_q, self.query_attr)

    def check(self, user, instance=None):
        if instance is None:
            return self.rule.check(user, None)
        related_q = self.rule.query(user)
        if related_q is UNIVERSAL or related_q is EMPTY:
            return related_q
        attr = instance.__class__._meta.get_field(self.query_attr,).get_accessor_name()
        related_manager = getattr(instance, attr)
        return related_manager.filter(related_q).exists()
