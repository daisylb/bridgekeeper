Bridgekeeper Legacy Documentation
=================================

.. note::

    This is the legacy documentation, taken from the internal project that Bridgekeeper was extracted from. As time goes on, sections will be taken from here and moved into an easier-to-understand structure.

Access control is defined by a list of **permissions**. Each permission has a name, in the form ``app_name.permission_name`` (by convention, usually ``app_name.action_modelname`` e.g. ``applicants.view_applicant``), and a **predicate**, which you can think of as a function that takes a user and a model instance and returns ``True`` or ``False``. (They're a little more complicated than that, but we'll cover that later.)

Checking permissions
::::::::::::::::::::

Bridgekeeper hooks into Django's authorisation framework, so if you have a :class:`~django.contrib.auth.models.User` object, you can just use that::

    user.has_perm('applicants.view_applicant', obj=applicant)

You can also call ``has_perm`` without an ``obj`` parameter, which is useful for permissions that don't relate to database objects, such as this hypothetical example::

    user.has_perm('foo.can_send_email')

If you call ``has_perm`` on a permission that *does* relate to a database object (e.g. ``applicants.view_applicant`` above), ``bridgekeeper`` will return ``True`` if and only if it knows that user *always* has that permission on *every row that could possibly exist in the database*. Usually this call shouldn't actually hit the database. (We'll discuss this in depth when we get to defining permissions, below.)

.. _has-module-perms:

``has_module_perms``
....................

Bridgekeeper also supports ``has_module_perms``::

    user.has_module_perms('applicants')

Unlike ``has_perm``, Bridgekeeper will return ``True`` from a ``has_module_perms('applicants')`` call if it thinks the user has any permission in the ``applicants`` module on *any row that could possibly exist in the database*, even if there are no such rows at the moment. (Put another way, it will only return ``False`` if the user never has and could not possibly have any permission in that app on any row that could possibly exist.)

This behaviour is different to ``has_perm`` because ``has_module_perms`` is likely to be used to show and hide entire parts of a project, navigation items, and so on. Consider a user that is allowed to view *some* applicants, but no such applicant currently exists in the database; generally, you want that user to be able to navigate to the applicant view, see an empty list, and possibly create one; hiding all the applicant views is likely to be more confusing.

To perform an equivalent test on a single permission, call
:meth:`~bridgekeeper.predicates.Predicate.is_possible_for` on it.

Filtering QuerySets by permissions
..................................

Most of the time, rather than checking permissions against an object you've already retrieved, you'll want to take a QuerySet and filter it down to just the objects that a particular user has some permission on, especially if your app restricts view permissions.

You can do that by extracting a particular permission's predicate out of the registry, and calling its ``filter`` method::

    from bridgekeeper.registry import registry

    filtered_qs = registry['applicants.view_applicant'].filter(queryset, user)

``filtered_qs`` is an ordinary query set that you can take and iterate over, filter further, paginate, and so on.

.. note::

    Currently, there is no way to distinguish between the case where a user doesn't have and could not possibly have a particular permission at all, and the case where a user could have a permission for some objects in the database, when filtering QuerySets.

Using permissions in views
..........................

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
        permission_name = 'applicants.create_applicant'
        model = Applicant

.. note::

    Unlike ``QuerySetPermissionMixin``, ``CreatePermissionGuardMixin`` is only a safety net; you still need to write your forms and views so that a user can't create instances they shouldn't be allowed to, but the mixin will protect you against logic errors in your code, possibly combined with malicious users.

Defining permissions
::::::::::::::::::::

We mentioned earlier that permissions are a mapping of names to predicates. Predicates are instances of (subclasses of) the :class:`~bridgekeeper.predicates.Predicate` class, and the mapping is stored in the :class:`~bridgekeeper.registry.registry`, which acts like a dictionary::

    from bridgekeeper.predicates import Attribute, is_staff
    from bridgekeeper.registry import registry

    registry['foo.update_widget'] = is_staff

The :mod:`~bridgekeeper.predicates` module provides a range of pre-made predicate instances as well as predicate classes you can instantiate, as shown above. You can also combine predicates using the ``&`` (and), ``|`` (or), and ``~`` (not) operators::

    registry['foo.view_widget'] = is_staff | Attribute(
        'company', lambda user: user.company)

Finally, if none of the built-in predicates do what you want, you can subclass :class:`~bridgekeeper.predicates.Predicate` yourself and write your own; see its API documentation for details.
