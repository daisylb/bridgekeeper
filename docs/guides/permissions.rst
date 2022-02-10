Checking Permissions
====================

There are two ways to check which permissions a user has using Bridgekeeper.

- Use the methods on the :class:`~django.contrib.auth.models.User` model, which consult Bridgekeeper via its integration into Django's pluggable authorisation system. You can only make the types of checks Django has built-in support for this way, which means you can't check against QuerySets. Also, if you have multiple different authorisation backends (including Django's built in :class:`~django.contrib.auth.backends.ModelBackend`), these methods will consult all of them.
- Check against permissions in Bridgekeeper directly. This is the only way to filter QuerySets according to a permission; this method always uses the permissions defined in Bridgekeeper as a single source of truth and does not consult other backends.

Checking Permissions on an Object
---------------------------------

Given an instance of our ``Shrubbery`` model called ``shrubbery``, and a :class:`~django.contrib.auth.models.User` instance ``user``, here's how we'd check to see whether the user has permission to update it::

    from bridgekeeper import perms

    # through Django:
    user.has_perm('shrubberies.change_shrubbery', obj=shrubbery)
    # or through Bridgekeeper:
    perms['shrubberies.change_shrubbery'].check(user, shrubbery)

Both of these expressions will return either ``True`` or ``False``. Aside from the caveat described above regarding authorisation backends other than Bridgekeeper, these two calls are equivalent; in fact, when you call :meth:`~django.contrib.auth.models.User.has_perm`, Django will trigger a call to :meth:`~bridgekeeper.rules.Rule.check` under the hood.

Checking Permissions on a QuerySet
----------------------------------

Of course, Bridgekeeper's headline feature is that it works with QuerySets; given a user and a permission, it can filter down a QuerySet to only return instances for which the user holds the permission.

All we need to do is call :meth:`~bridgekeeper.rules.Rule.filter` instead of :meth:`~bridgekeeper.rules.Rule.check`, and pass it a QuerySet instead of a single model instance::

    qs = models.Shrubbery.objects.all()
    filtered_qs = perms['shrubberies.view_shrubbery'].filter(user, qs)

Bridgekeeper's :meth:`~bridgekeeper.rules.Rule.filter` takes any QuerySet, and returns another normal QuerySet (it actually just calls the QuerySet's :meth:`~django.db.models.query.QuerySet.filter` method internally). This means you can call :meth:`~django.db.models.query.QuerySet.filter`, :meth:`~django.db.models.query.QuerySet.exclude` or :meth:`~django.db.models.query.QuerySet.order_by` your QuerySet before you pass it in, or you can :meth:`~django.db.models.query.QuerySet.filter`, :meth:`~django.db.models.query.QuerySet.exclude`, :meth:`~django.db.models.query.QuerySet.order_by`, slice or paginate the QuerySet that Bridgekeeper returns to you.

Checking Permissions For All Possible Instances
-----------------------------------------------

Django's :meth:`~django.contrib.auth.models.User.has_perm` (and thus also Bridgekeeper's :meth:`~bridgekeeper.rules.Rule.check`) allows supplying only a permission name, and not an object instance::

    user.has_perm('shrubberies.view_shrubbery')
    # or,
    perms['shrubberies.view_shrubbery'].check(user)

Once again, these calls are equivalent, aside from the caveat described above regarding authorisation backends other than Bridgekeeper.

When you check permissions like this without supplying an instance, Bridgekeeper will return ``True`` if and only if the user has that permission **for every possible instance that could ever exist**. (This is not the same thing as checking whether the user has the permission for every instance *currently in the database*; in fact, this check doesn't actually hit the database at all.)

As an example of this, let's say that the ``shrubberies.view_shrubbery`` permission was defined to allow staff users access to all shrubberies, and everyone else access to shrubberies in their own branch::

    perms['shrubberies.view_shrubbery'] = is_staff | R(branch=lambda user: user.profile.branch)

In this case, the check would return ``True`` for a staff user, since they will always have access to every possible shrubbery. It will return ``False`` for a regular user, even if every shrubbery currently in the database belongs to their branch, because it is possible for a shrubbery to be created that belongs to a different branch, which they would then be blocked from editing.

Checking Permissions For *Any* Possible Instances
-------------------------------------------------

Bridgekeeper also provides a second method, :meth:`~bridgekeeper.rules.is_possible_for`, which is the opposite of the above behaviour, in a way::

    perms['shrubberies.change_shrubbery'].is_possible_for(user)

This check will return ``True`` if and only if the user could possibly have that permission for **any possible instance that could exist**. (Once again, this is not the same as checking whether the user has the permission for at least one instance *currently in the database*, and once again it doesn't actually hit the database at all.)

As an example of this, let's say that the ``shrubberies.view_shrubbery`` permission was defined to allow only shrubbers to edit shrubberies inside their own branch, using the ``is_shrubber`` rule we created in the :ref:`tutorial-blanket` section of the tutorial and combining it with an :class:`~bridgekeeper.rules.Attribute` check::

    perms['shrubberies.view_shrubbery'] = is_shrubber & R(branch=lambda user: user.profile.branch)

In this case, the check will return ``False`` for a user with the ``'apprentice'`` role, because only users with the ``'shrubber'`` role can access anything. It will always return ``True`` for a shrubber, however, even if there are no shrubberies belonging to their branch currently in the database, beacuse it is possible for a shrubbery to exist that belongs to their branch, which they would then be allowed to edit.

.. note::

    The behaviours in this section are effectively implemented by checking whether a permission is always allowed (in the case of :meth:`~bridgekeeper.rules.Rule.check`) or always denied (in the case of :meth:`~bridgekeeper.rules.is_possible_for`) due to the presence of blanket rules.

    In normal use, these methods should always behave how you'd expect. However, if you create a combination of rules that just happens to be tautological for a particular user, Bridgekeeper isn't clever enough to detect that.

    This also means that the checks described in this section usually won't need to hit the database.

``has_module_perms()``
::::::::::::::::::::::

Bridgekeeper also supports Django's :meth:`~django.contrib.auth.models.User.has_module_perms` method. The following call::

    user.has_module_perms('shrubberies')

is equivalent to calling :meth:`~bridgekeeper.rules.is_possible_for` on every permission whose name begins with ``shrubberies.``, and returning ``True`` if any one of them returns ``True``.

Permission Check Summary
------------------------

+---------------------------------+-------------------------------+-----------------------------------------+
|             Meaning             |            Django             |              Bridgekeeper               |
+=================================+===============================+=========================================+
| User has permission ``foo.bar`` | ``u.has_perm('foo.bar', x)``  | ``perms['foo.bar'].check(u, x)``        |
| for object ``x``                |                               |                                         |
+---------------------------------+-------------------------------+-----------------------------------------+
| User has permission ``foo.bar`` | ``u.has_perm('foo.bar')``     | ``perms['foo.bar'].check(u)``           |
| for all possible objects        |                               |                                         |
+---------------------------------+-------------------------------+-----------------------------------------+
| It is possible for the user to  | *n/a*                         | ``perms['foo.bar'].is_possible_for(u)`` |
| have permission ``foo.bar`` for |                               |                                         |
| some object                     |                               |                                         |
+---------------------------------+-------------------------------+-----------------------------------------+
| It is possible for the user to  | ``u.has_module_perms('foo')`` | *n/a*                                   |
| have some permission ``foo.*``  |                               |                                         |
| for some object                 |                               |                                         |
+---------------------------------+-------------------------------+-----------------------------------------+
| Filter the queryset ``qs`` to   | *n/a*                         | ``perms['foo.bar'].filter(u, qs)``      |
| only the objects that the user  |                               |                                         |
| has permission ``foo.bar`` for  |                               |                                         |
+---------------------------------+-------------------------------+-----------------------------------------+

Using permissions in views
--------------------------

Bridgekeeper provides a ``QuerySetPermissionMixin``, which will filter a view down to only objects that the currently logged-in user has access to. It works on ``ListView``, ``DetailView``, and most views that operate on the database except ``CreateView``, and is used like this::

    from bridgekeeper.mixins import QuerySetPermissionMixin

    class MyView(QuerySetPermissionMixin, DetailView):
        permission_name = 'applicants.view_applicant'
        model = Applicant

.. caution::

    ``QuerySetPermissionMixin`` will return 404 both for objects that don't exist and objects the user can't access. It might be tempting to try to distinguish between an the two, by returning e.g. 404 for the former and 403 for the latter. Generally, though, it's desirable from a security perspective to not let the user tell the difference between these two cases unless you really need to.

    If you're concerned about users getting unexpected 404s when they try to access a page without being logged in, one alternative is to reword your ``404.html`` accordingly, or even embed a login form there if users aren't logged in.

Bridgekeeper also provides ``CreatePermissionGuardMixin``, which will validate unsaved model instances in a ``CreateView`` (or any subclass of ``ModelFormView``) against a given permission, and raise :class:`~django.core.exceptions.SuspiciousOperation`, thus preventing the call to ``.save()``, if it does not pass. It's used like this::

    from bridgekeeper.mixins import CreatePermissionGuardMixin

    class MyView(CreatePermissionGuardMixin, CreateView):
        permission_name = 'applicants.add_applicant'
        model = Applicant

.. note::

    Unlike ``QuerySetPermissionMixin``, ``CreatePermissionGuardMixin`` is only a safety net; you still need to write your forms and views so that a user can't create instances they shouldn't be allowed to, but the mixin will protect you against logic errors in your code, possibly combined with malicious users.
