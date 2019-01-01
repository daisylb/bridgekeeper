Rules
=====

.. automodule:: bridgekeeper.rules

    The ``Rule`` API
    ----------------

    .. autoclass:: Rule
        :members: filter, check, is_possible_for

    Built-in Blanket Rules
    ----------------------

    .. data:: always_allow

        Rule that always allows access to everything.

    .. data:: always_deny

        Rule that never allows access to anything.

    .. data:: is_authenticated

        Rule that allows access to users for whom
        :attr:`~django.contrib.auth.models.User.is_authenticated` is ``True``.

    .. data:: is_superuser

        Rule that allows access to users for whom
        :attr:`~django.contrib.auth.models.User.is_superuser` is ``True``.

    .. data:: is_staff

        Rule that allows access to users for whom
        :attr:`~django.contrib.auth.models.User.is_staff` is ``True``.

    .. data:: is_active

        Rule that allows access to users for whom
        :attr:`~django.contrib.auth.models.User.is_active` is ``True``.

    Rule Classes
    ------------

    .. autoclass:: Attribute

    .. autoclass:: Relation

    .. autoclass:: ManyRelation

    .. autoclass:: Is

    .. autoclass:: In

    Built-in rule instances
    -----------------------

    .. autodata:: current_user

    .. autodata:: in_current_groups

    Extension Points (For Writing Your Own ``Rule`` Subclasses)
    ----------------

    .. class:: Rule

        If you want to create your own rule class, these are the methods you
        need to override.

        .. automethod:: query

        .. automethod:: check

    .. autodata:: UNIVERSAL

    .. autodata:: EMPTY
