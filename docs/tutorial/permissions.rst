Defining Permissions
====================

In this tutorial, we'll be using a example app, an online stock management portal for shrubberies; we'll define some permissions for it in this section, then use them in views in the next section. It has a single app called ``shrubberies``, with a ``models.py`` looks something like this:

.. code-block:: python
    :caption: shrubberies/models.py

    from django.contrib.auth.models import User
    from django.db import models


    class Store(models.Model):
        name = models.CharField(max_length=255)


    class Branch(models.Model):
        store = models.ForeignKey(Store, on_delete=models.CASCADE)
        name = models.CharField(max_length=255)


    class Shrubbery(models.Model):
        branch = models.ForeignKey(Branch, on_delete=models.PROTECT)
        name = models.CharField(max_length=255)
        price = models.DecimalField(max_digits=5, decimal_places=2)


    class Profile(models.Model):
        """User profile.

        Every user has one Profile object attached to them, which is
        automatically created when the user is added, and holds information
        about which branch of which store they belong to and what their
        role is.
        """

        user = models.OneToOneField(User, on_delete=models.CASCADE)
        branch = models.ForeignKey(Branch, on_delete=models.PROTECT)
        role = models.CharField(max_length=16, choices=(
            ('apprentice', 'Apprentice Shrubber'),
            ('shrubber', 'Shrubber'),
        ))

Defining Our First Permission
-----------------------------

In Bridgekeeper, permissions are defined by **rules**. A rule is an object that can be given a user and a model instance, and decides whether or not to allow that user access to that instance.

.. note::

    From that description, you might be thinking that a rule object is just a function with the signature ``(user, model_instance) -> bool``. While you can certainly think of them that way, internally they're a little more complex than that, for reasons that will become apparent in the next section.

One of the simplest rules in Bridgekeeper is the built-in :data:`~bridgekeeper.rules.is_staff` rule, which answers "yes" if the user trying to log in has :attr:`~django.contrib.auth.models.User.is_staff` set, or "no" otherwise.

We turn a rule into a **permission** by assigning it to a name. We do that by creating a file called ``permissions.py`` inside our app, importing :data:`bridgekeeper.perms` (which is a Python dictionary [#permissionmap]_ that maps permission names to their corresponding rules) and adding entries to it.

.. code-block:: python
    :caption: shrubberies/permissions.py

    from bridgekeeper import perms
    from bridgekeeper.rules import is_staff

    perms['shrubbery.create_store'] = is_staff
    perms['shrubbery.update_store'] = is_staff
    perms['shrubbery.delete_store'] = is_staff


.. note::

    We've used permission names that follow the convention set by :ref:`Django's built-in permissions mechanism <django:topic-authorization>`, so that they're used by other apps that expect that naming convention, such as Django's built-in admin. You can use whatever permission names you like, although it's best to namespace them with the name of your app followed by a full stop at the start (e.g. ``shrubbery.foo``).

These permissions are now fully working; if you wanted, you could skip right through to the next section to see how to use them in your views. Don't, though, because Bridgekeeper is capable of far more.

.. _tutorial-blanket:

Blanket Rules
-------------

Blanket rules are rules whose outcome is only affected by the user. We said earlier that rules are *questions to ask about the user that is trying to gain access, and the objects they're trying to gain access to*; blanket rules are *questions to ask about the user that is trying to gain access*, without regard for what they're accessing.

The built-in rule :data:`~bridgekeeper.rules.is_staff` is an blanket rule, as are :data:`~bridgekeeper.rules.is_authenticated`, :data:`~bridgekeeper.rules.is_superuser` and :data:`~bridgekeeper.rules.is_active`.

We can define our own, too, by using the :class:`~bridgekeeper.rules.blanket_rule` decorator to wrap a function that takes a user and returns a boolean:

.. code-block:: python
    :caption: shrubberies/rules.py

    from bridgekeeper.rules import blanket_rule

    @blanket_rule
    def is_apprentice(user):
        return user.profile.role == 'apprentice'

    @blanket_rule
    def is_shrubber(user):
        return user.profile.role == 'shrubber'

If we wanted to restrict the ability to edit shrubberies in our app to only users that have the Shrubber role, we could write something like this:

.. code-block:: python
    :caption: shrubberies/permissions.py

    from .rules import is_shrubber

    perms['shrubbery.update_shrubbery'] = is_shrubber

Matching Against Model Instance Attributes
------------------------------------------

Blanket rules let us allow or deny access to entire model classes based on the user, but we can also allow access to only certain instances. Consider the following requirement:

    Users can only edit shrubberies that belong to their branch.

We can model this as a Bridgekeeper rule by creating an instance of the :class:`~bridgekeeper.rules.Attribute` class:

.. code-block:: python
    :caption: shrubberies/permissions.py

    from bridgekeeper.rules import Attribute

    perms['shrubbery.update_shrubbery'] = Attribute('branch', lambda user: user.profile.branch)

You can think of :class:`~bridgekeeper.rules.Attribute` as the Bridgekeeper equivalent to the standard library's :func:`getattr` function. It will only allow access when the attribute named in the first argument (here, ``'branch'``) matches whatever is in the second argument. The second argument can either be a constant, or—as we've used here—a function that takes the current user and returns something to match against.

Traversing Relationships
------------------------

What if we change the requirement to something like this?

    Users can only edit shrubberies that belong to their store.

Shrubberies don't have a ``store`` attribute; we have to go through the ``branch`` attribute to figure out which store a shrubbery belongs to, so we can't use :class:`~bridgekeeper.rules.Attribute`.

This is where the :class:`~bridgekeeper.rules.Relation` class comes in. :class:`~bridgekeeper.rules.Relation` is similar to :class:`~bridgekeeper.rules.Attribute`, but instead of taking a constant or function as its last argument, it takes *another rule object*, which is applied to the other side of the relation.

.. note::

    :class:`~bridgekeeper.rules.Relation` currently takes three arguments. The first and last are described above, but the middle argument is the model class the relation points to.

    This argument will be removed before the 1.x release series; for more details see `issue #3`_.

 .. _`issue #3`: https://github.com/adambrenecki/bridgekeeper/issues/3


.. code-block:: python
    :caption: shrubberies/permissions.py

    from bridgekeeper.rules import Relation

    from . import models

    perms['shrubbery.update_shrubbery'] = Relation(
        'branch',
        models.Branch,
        # This rule gets checked against the branch object, not the shrubbery
        Attribute('store', lambda user: user.profile.branch.store),
    )


Combining Rules Together
------------------------

Rules, much like :class:`~django.db.models.Q` objects, can be combined using the ``|`` (or), ``&`` (and), and ``~`` (not) operators.

For instance, the expression ``~is_apprentice`` will return a new rule that is true for all users that aren't apprentices, and the expression ``is_staff | is_shrubber`` for all users that have the ``is_staff`` flag set, or that have the ``'shrubber'`` role in their profile.

For a more complex example, let's say that we wanted the following rule to apply:

    Administrative staff (with ``is_staff`` set) can edit all shrubberies in the system. Shrubbers can edit all shrubberies in the store they belong to. Apprentice shrubbers can edit all shrubberies in their branch.

We can implement that behaviour with the following permission:

.. code-block:: python
    :caption: shrubberies/permissions.py

    from bridgekeeper.rules import is_staff
    from .rules import is_shrubber, is_apprentice
    from . import models

    perms['shrubbery.update_shrubbery'] = is_staff | (
        is_apprentice & Attribute('branch', lambda user: user.profile.branch)
    ) | (
        is_shrubber & Relation(
            'branch', models.Branch, Relation(
                'store', models.Store, Is(lambda user: user.profile.branch.store),
            )
        )
    )

.. [#permissionmap] :data:`bridgekeeper.perms` is actually an instance of :class:`~bridgekeeper.permission_map.PermissionMap`, which is a subclass of :class:`dict` with a few small changes, but you can treat it as a normal dictionary anyway.
