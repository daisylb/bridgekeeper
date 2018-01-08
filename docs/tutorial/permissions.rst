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
        user = models.OneToOneField(User, on_delete=models.CASCADE)
        branch = models.ForeignKey(Branch, on_delete=models.PROTECT)
        role = models.CharField(max_length=16, choices=(
            ('apprentice', 'Apprentice Shrubber'),
            ('shrubber', 'Shrubber'),
        ))

Defining Our First Permission
-----------------------------

In Bridgekeeper, permissions are defined by **rules**. A rule is an object that represents a question to ask about the user trying to gain access to something and the something that they're trying to access, and gives a yes or no answer.

.. note::

    From that description, you might be thinking that a rule object is just a function that takes a user object and a model instance and returns a boolean. While you can certainly think of them that way, internally they're a little more complex than that, for reasons that will become apparent in the next section.

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

We can define our own, too, by using the :class:`~bridgekeeper.rules.blanket` decorator to wrap a function that takes a user and returns a boolean:

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

Model Rules
-----------

.. todo::

    Fill out this section

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
        is_apprentice & Relation(
            'branch', models.Branch, Is(lambda user: user.profile.branch),
        )
    ) | (
        is_shrubber & Relation(
            'branch', models.Branch, Relation(
                'store', models.Store, Is(lambda user: user.profile.branch.store),
            )
        )
    )

.. [#permissionmap] :data:`bridgekeeper.perms` is actually an instance of :class:`~bridgekeeper.permission_map.PermissionMap`, which is a subclass of :class:`dict` with a few small changes, but you can treat it as a normal dictionary anyway.
