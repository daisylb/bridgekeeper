Using Permissions In Views
==========================

Now that we've got our permissions defined, we need to write views that actually use them. If you've already used Django's built-in permission mechanism, Bridgekeeper integrates with that:

.. code-block:: python
    :caption: shrubberies/views.py
    :emphasize-lines: 9

    from django.http import Http404
    from django.shortcuts import get_object_or_404
    from django.template.response import TemplateResponse

    from . import models

    def shrubbery_edit(request, shrubbery_id):
        shrubbery = get_object_or_404(models.Shrubbery, id=shrubbery_id)
        if not request.user.has_perm('shrubberies.update_shrubbery', shrubbery):
            raise Http404()
        return TemplateResponse(request, 'shrubbery_edit.html', {
            'shrubbery': shrubbery,
        })

We can also check permissions directly through Bridgekeeper. Remember, :data:`bridgekeeper.perms` is more or less just a dict, so we can pull it out of there and call the rule's :meth:`~bridgekeeper.rules.Rule.check` method:

.. code-block:: python
    :caption: shrubberies/views.py
    :emphasize-lines: 5

    from bridgekeeper import perms

    def shrubbery_edit(request, shrubbery_id):
        # ...
        if not perms['shrubberies.update_shrubbery'].check(request.user, shrubbery):
            raise Http404()
        # ...

.. note::

    If you use Django's :meth:`~django.contrib.auth.models.User.has_perm`, like in our first example, Django will consult *all* of your authentication backends to check permissions. For instance, if you've assigned permissions to users in your database through Django's built-in :attr:`~django.contrib.auth.models.User.user_permissions`, they'll be checked as well. Similarly, if you have a third-party authentication backend (e.g. for social media, LDAP or Active Directory integration) that provides some form of permission checking, that will be checked too.

    If you use Bridgekeeper directly, like in our second example, only Bridgekeeper permissions will be checked; in most cases this is what you want.

Filtering QuerySets
-------------------

If we're displaying a list, we can also filter a QuerySet so that it only contains objects that the currently-logged-in user holds a certain permission on.

.. code-block:: python
    :caption: shrubberies/views.py
    :emphasize-lines: 9

    from bridgekeeper import perms
    from django.core.paginator import Paginator
    from django.template.response import TemplateResponse

    from . import models

    def shrubbery_list(request, shrubbery_id):
        all_shrubberies = models.Shrubbery.objects.all()
        shrubberies = perms['shrubberies.view_shrubbery'].filter(request.user, all_shrubberies)

        # 'shrubberies' is just a regular queryset, so we can do anything
        # we would do with a normal queryset; in this case, let's paginate it
        paginator = Paginator(shrubberies, 10)
        page = paginator.page(1)

        return TemplateResponse(request, 'shrubbery_list.html', {
            'paginator': paginator,
            'page': page,
            'shrubberies': page.object_list,
        })


Class-Based Views
-----------------

All of the examples we've used so far have been function-based views. Of course, everything that we've covered so far will work inside a class-based view, but Bridgekeeper also comes with a handy shortcut in the form of :class:`~bridgekeeper.mixins.QuerySetPermissionMixin`.

.. code-block:: python
    :caption: shrubberies/views.py
    :emphasize-lines: 7, 9, 12, 14

    from bridgekeeper.mixins import QuerySetPermissionMixin
    from django.views.generic import ListView, UpdateView

    from . import models


    class ShrubberyListView(QuerySetPermissionMixin, ListView):
        model = models.Shrubbery
        permission_name = 'shrubberies.view_shrubbery'


    class ShrubberyUpdateView(QuerySetPermissionMixin, UpdateView):
        model = models.Shrubbery
        permission_name = 'shrubberies.update_shrubbery'

That's all there is to it; these two views will now only show shrubberies that the currently-logged-in user has permission to view.

What next?
----------

That's the end of the tutorial; you should now be able to get started modelling your permissions with Bridgekeeper now!

You can read about the other ways you can check permissions, including more convenience shortcuts you can enable and ways to check things like whether somebody *could, hypothetically, have* a permission in the :doc:`/guides/permissions` guide. Or, find out more detail about writing rules and permissions in the :doc:`/guides/rules` guide.

If there's something that you don't understand after following through this tutorial, or that you think could be explained better, please `file a documentation bug <docbug_>`_ so that we can improve the docs for future users.


.. _docbug: https://github.com/adambrenecki/bridgekeeper/issues/new?labels=docs
