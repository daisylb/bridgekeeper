Using Permissions In Views
==========================

Bridgekeeper integrates with Django's built-in user permissions mechanism, so you can use the :meth:`~django.contrib.auth.User.has_perm` method on a user object to check permissions:

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

We can also do the same thing directly through Bridgekeeper. Remember, :data:`bridgekeeper.perms` is more or less just a dict, so we can pull it out of there and call the rule's :meth:`~bridgekeeper.rules.Rule.check` method:

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

    If you're *only* using Bridgekeeper for authorization, these two examples will be equivalent. If you've got permissions set in Django's built in :class:`~django.contrib.auth.models.Permission` model, or another authentication backend, the former example will query them too, but the latter will only consult Bridgekeeper.
