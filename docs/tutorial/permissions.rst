Defining permissions
====================

In this tutorial, we'll be using a example app, an online stock management portal for shrubberies. We'll define some permissions for it in this section, then use them in views in the next section. It has a single app called ``shrubberies``, with a ``models.py`` looks something like this:

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

Defining our first permission
-----------------------------

In Bridgekeeper, permissions are defined by **rules**. A rule is an object that can be given a user and a model instance, and decides whether or not to allow that user access to that instance.

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

Blanket rules
-------------

A blanket rule is a rule that decides whether or not to allow access based solely on the user that's trying to access the resource. They can't allow access to some objects but not others; they're solely all-or-nothing, hence the name.

We've already used one blanket rule—the built-in :data:`~bridgekeeper.rules.is_staff` rule—but we can also define our own, by using the :class:`~bridgekeeper.rules.blanket_rule` decorator to wrap a function that takes a user and returns a boolean.

In this example, we're using the ``role`` attribute on each user's associated ``Profile`` instance to restrict access to users that have been assigned a particular role:

.. code-block:: python
    :caption: shrubberies/rules.py

    from bridgekeeper.rules import blanket_rule

    @blanket_rule
    def is_apprentice(user):
        return user.profile.role == 'apprentice'

    @blanket_rule
    def is_shrubber(user):
        return user.profile.role == 'shrubber'

If we were given a requirement like this:

    Only shrubbers can edit shrubberies.


We could use our new ``is_shrubber`` rule the same way that we used ``is_staff`` before:

.. code-block:: python
    :caption: shrubberies/permissions.py

    from .rules import is_shrubber

    perms['shrubbery.update_shrubbery'] = is_shrubber

Matching against model instances
--------------------------------

Blanket rules let us allow or deny access to entire model classes based on the user, but we can also allow access to only certain instances.

To start with, we'll use a rather contrived requirement to start with:

    Users can only edit shrubberies that cost $5.

To do this, we'll use an :class:`~bridgekeeper.rules.R` object. :class:`~bridgekeeper.rules.R` objects are a kind of Bridgekeeper rule that can filter model instances; they look kind of like a Django :class:`~django.db.models.Q` object or the :meth:`~django.db.models.QuerySet.filter` method on a Django queryset.

.. code-block:: python
    :caption: shrubberies/permissions.py

    from bridgekeeper.rules import R

    perms['shrubbery.update_shrubbery'] = R(price=5)

That's fairly useless, but it works! Let's move on to a slightly more useful requirement:

    Users can only edit shrubberies that belong to their branch.

We have a problem here: we can't just say ``R(branch=SOME_BRANCH)``, where ``SOME_BRANCH`` is a constant, because *which* branch we want to filter against will be different for different users [#modelconstant]_.

Fortunately, if you pass a callable to an :class:`~bridgekeeper.rules.R` object, when it's used it'll call that callable with a user instance as an argument, and whatever gets returned is the thing that'll get checked against.

.. code-block:: python
    :caption: shrubberies/permissions.py

    perms['shrubbery.update_shrubbery'] = R(branch=lambda user: user.profile.branch)

Traversing relationships
------------------------

What if we change the requirement to something like this?

    Users can only edit shrubberies that belong to any branch in the same store as them.

Shrubberies don't have a ``store`` attribute; we have to go through the ``branch`` attribute to figure out which store a shrubbery belongs to. We can do that using the same double-underscore notation that :class:`~django.db.models.Q` uses.

.. code-block:: python
    :caption: shrubberies/permissions.py

    perms['shrubbery.update_shrubbery'] = R(branch__store=lambda user: user.profile.branch.store)


Combining rules together
------------------------

All of the rules that we've seen so far are quite simple, each only checking one thing. Fortunately, Bridgekeeper rules can be combined together, letting us model much more complex requirements.

We do this using the ``&``, ``|`` and ``~`` operators.

- Prefixing a rule with ``~`` inverts it. For example, the expression ``~is_apprentice`` returns a rule that allows access to everyone that is **not** an apprentice shrubber.
- Combining two rules with ``|`` allows access if *either* rule matches. For example, ``is_staff | is_shrubber`` allows access to users that are either administrative staff **or** shrubbers.
- Combining two rules with ``&`` allows access if *both* rules match. For example, ``is_staff & is_shrubber`` allows access to users that are both administrative staff **and** shrubbers.

For a more complex example, let's say that we needed to model the following requirement:

    Administrative staff (with ``is_staff`` set) can edit all shrubberies in the system. Shrubbers can edit all shrubberies in the store they belong to. Apprentice shrubbers can edit all shrubberies in their branch.

First, we need to rephrase this requirement so that it's made up of simpler rules combined with **and**, **or**, and **not**.

    Users can edit shrubberies if:

    - They are administrative staff (with ``is_staff`` set), **or**
    - They are a shrubber, **and** the shrubbery belongs to the same store as them, **or**
    - They are an apprentice shrubber, **and** the shrubbery belongs to the same branch as them

In earlier sections of this chapter, we've already talked about rules that allow access to staff users and users with particular roles. We've also already discussed rules that allow access only to shrubberies belonging to the same store or branch as the user trying to access them. All we need to do now is combine them together:

.. code-block:: python
    :caption: shrubberies/permissions.py

    from bridgekeeper.rules import is_staff
    from .rules import is_shrubber, is_apprentice
    from . import models

    perms['shrubbery.update_shrubbery'] = is_staff | (
        is_shrubber & R(branch__store=lambda user: user.profile.branch.store)
    ) | (
        is_apprentice & R(branch=lambda user: user.profile.branch)
    )

.. [#permissionmap] :data:`bridgekeeper.perms` is actually an instance of :class:`~bridgekeeper.permission_map.PermissionMap`, which is a subclass of :class:`dict` with a few small changes, but you can treat it as a normal dictionary anyway.
.. [#modelconstant] Of course, this is one of multiple reasons we can't do this, the other having to do with accessing the database at import time in order to define such a constant, which is a bad idea, but that's rather academic.
