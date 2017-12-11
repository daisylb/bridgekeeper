Installing Bridgekeeper
=======================

First, install the ``bridgekeeper`` package from PyPI.

.. code-block:: sh

    $ pip install bridgekeeper
    # or, if you're using pipenv
    $ pipenv install bridgekeeper

Then, add Bridgekeeper to your ``settings.py``:

.. code-block:: diff

     INSTALLED_APPS = (
         'django.contrib.admin',
         'django.contrib.auth',
         # ...
    +    'bridgekeeper',
     )

     # ...

     AUTHENTICATION_BACKENDS = (
         'django.contrib.auth.backends.ModelBackend',
    +    'bridgekeeper.backends.RulePermissionBackend',
     )

.. note::

    Order doesn't matter for either the :setting:`INSTALLED_APPS` or :setting:`AUTHENTICATION_BACKENDS` entry.

    You might not already have the :setting:`AUTHENTICATION_BACKENDS` setting in your ``settings.py``; if not, you'll have to add it.
