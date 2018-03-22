Django REST Framework integration
=================================

Installation
------------

If you want to use Django REST Framework and Bridgekeeper together, you'll need to add the following to your ``settings.py``::

    REST_FRAMEWORK = {
        'DEFAULT_PERMISSION_CLASSES': (
            'bridgekeeper.rest_framework.RulePermissions',
        )
        'DEFAULT_FILTER_BACKENDS': ('bridgekeeper.rest_framework.RuleFilter',)
    }

.. info::

    Bridgekeeper needs to provide both a filter backend and a permission class, because permission classes can't filter querysets on their own. Don't worry, the filter backend should work just fine alongside whichever other filter backends you're using.

.. warning::

    These settings only set the *default* permission classes and filter backends. If you override either ``permission_classes`` or ``filter_backends`` in any ``APIView`` or ``ViewSet`` subclass, you'll need to make sure Bridgekeeper's classes are included in those locations too.

Permission Naming
-----------------

Once you've changed your settings, all of your API views will automatically apply the appropriate permissions. In order for them to do so, they need to be named according to the conventional Django permission naming scheme. Given a Django app called ``app_name`` and a model called ``ModelName``, the following permissions will be checked:

- ``app_name.view_modelname`` for all requests.
- ``app_name.add_modelname`` for ``POST`` requests.
- ``app_name.change_modelname`` for ``PUT`` and ``PATCH`` requests.
- ``app_name.delete_modelname`` for ``DELETE`` requests.

One side-effect of this is that your API consumers will not be able to make changes if they have ``add``, ``change`` or ``delete`` permissions on some object but don't also have ``view`` permissions for that same object. That being said, it doesn't make sense for a user to be able to change something they can't see anyway.
