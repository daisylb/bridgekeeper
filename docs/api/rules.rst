Rules
=====

.. automodule:: bridgekeeper.rules
    :members:

    .. data:: always_allow

        Rule that is always satisfied.

    .. data:: always_deny

        Rule that is never satisfied.

    .. data:: is_authenticated
    .. data:: is_superuser
    .. data:: is_staff
    .. data:: is_active

        Equivalent to checking the
        :attr:`~django.contrib.auth.models.User.is_authenticated`,
        :attr:`~django.contrib.auth.models.User.is_superuser`,
        :attr:`~django.contrib.auth.models.User.is_staff`, or
        :attr:`~django.contrib.auth.models.User.is_active` attributes on
        :class:`~django.contrib.auth.models.User`, respectively.
