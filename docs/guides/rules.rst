Writing Rules
=============

Rules are instances of (subclasses of) the :class:`~bridgekeeper.rules.Rule` class. Permissions are a mapping from a permission name (which is a string) the mapping is stored in :data:`bridgekeeper.perms`, which acts like a dictionary::

    from bridgekeeper.rules import Attribute, is_staff
    from bridgekeeper import perms

    perms['foo.update_widget'] = is_staff

The :mod:`~bridgekeeper.rules` module provides a range of pre-made rule instances as well as rule classes you can instantiate, as shown above. You can also combine rules using the ``&`` (and), ``|`` (or), and ``~`` (not) operators::

    perms['foo.view_widget'] = is_staff | Attribute(
        'company', lambda user: user.company)

Finally, if none of the built-in rules do what you want, you can subclass :class:`~bridgekeeper.rules.Rule` yourself and write your own.


Ambient Rules
-------------

We introduced what ambient rules are, as well as how to write a custom one, in the :ref:`tutorial-ambient` section of the tutorial. There, we defined one rule for each role, but if we had more than two roles that might get a bit repetitive.

If you need your ambient rules to take arguments, the easiest way is to write a function that *returns* a rule, like so:

.. code-block:: python
    :caption: shrubberies/rules.py

    from bridgekeeper.rules import ambient

    def has_role(role):

        def checker(user):
            return user.profile.role == role

        return ambient(checker, repr_string=f"has_role({role!r})")

In this case, we're using the optional ``repr_string`` argument to override how the rule is displayed when debugging, so that we can see what the ``role`` argument is. (We're using `PEP 498`_ f-strings here, which are supported in Python 3.6+, but you don't have to.)

.. _PEP 498: https://www.python.org/dev/peps/pep-0498/
