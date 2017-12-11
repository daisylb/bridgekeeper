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


First, we'll define permissions for our ``Store`` model. We'll define them in ``permissions.py``, because that's where Bridgekeeper will automatically load them from.

:ref:`Permissions in Django <django:topic-authorization>` typically have names of the form ``appname.action_modelname``, where ``appname`` is the app name (``shrubbery`` in our case), ``modelname`` is the lowercased version of the model name, and ``action`` is one of ``create``, ``update`` or ``delete``. So, the permissions we want to create, we'll call ``shrubbery.create_store``, ``shrubbery.update_store`` and ``shrubbery.delete_store``.

In Bridgekeeper, permissions are made up of **predicates**, which you can think of as questions to ask about the user that is trying to gain access, and the objects they're trying to gain access to. For the ``Store`` model, we only want the administrators of our marketplace to be able to manipulate stores, so we can use the built-in :data:`~bridgekeeper.predicates.is_staff` predicate, which asks "Is the user a staff user?":

.. code-block:: python
    :caption: shrubberies/permissions.py

    from bridgekeeper import perms
    from bridgekeeper.predicates import is_staff

    perms['shrubbery.create_store'] = is_staff
    perms['shrubbery.update_store'] = is_staff
    perms['shrubbery.delete_store'] = is_staff

We turn predicates into permissions by putting them into :data:`bridgekeeper.perms`, which is a Python dictionary that maps permission names to their predicates. (It's actually a custom subclass of :class:`dict` with a few small changes, but you can treat it as if it's a normal dictionary anyway.)

These permissions are now fully working; if you wanted, you could skip right through to the next section to see how to use them in your views. Don't, though, because we've just scratched the surface.

.. _tutorial-ambient:

Ambient Predicates
------------------

Ambient predicates are predicates whose outcome is only affected by the user. We said earlier that predicates are *questions to ask about the user that is trying to gain access, and the objects they're trying to gain access to*; ambient predicates are *questions to ask about the user that is trying to gain access*, without regard for what they're accessing.

The built-in predicate :data:`~bridgekeeper.predicates.is_staff` is an ambient predicate, as are :data:`~bridgekeeper.predicates.is_authenticated`, :data:`~bridgekeeper.predicates.is_superuser` and :data:`~bridgekeeper.predicates.is_active`.

We can define our own, too, by using the :class:`~bridgekeeper.predicates.ambient` decorator to wrap a function that takes a user and returns a boolean:

.. code-block:: python
    :caption: shrubberies/predicates.py

    from bridgekeeper.predicates import ambient

    @ambient
    def is_apprentice(user):
        return user.profile.role == 'apprentice'

    @ambient
    def is_shrubber(user):
        return user.profile.role == 'shrubber'

If we wanted to restrict the ability to edit shrubberies in our app to only users that have the Shrubber role, we could write something like this:

.. code-block:: python
    :caption: shrubberies/permissions.py

    from .predicates import is_shrubber

    perms['shrubbery.update_shrubbery'] = is_shrubber

Model Predicates
----------------

.. todo::

    Fill out this section

Combining Predicates Together
-----------------------------

Predicates, much like :class:`~django.db.models.Q` objects, can be combined using the ``|`` (or), ``&`` (and), and ``~`` (not) operators.

For instance, the expression ``~is_apprentice`` will return a new predicate that is true for all users that aren't apprentices, and the expression ``is_staff | is_shrubber`` for all users that have the ``is_staff`` flag set, or that have the ``'shrubber'`` role in their profile.

For a more complex example, let's say that we wanted the following rule to apply:

    Administrative staff (with ``is_staff`` set) can edit all shrubberies in the system. Shrubbers can edit all shrubberies in the store they belong to. Apprentice shrubbers can edit all shrubberies in their branch.

We can implement that behaviour with the following permission:

.. code-block:: python
    :caption: shrubberies/permissions.py

    from bridgekeeper.predicates import is_staff
    from .predicates import is_shrubber, is_apprentice
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
