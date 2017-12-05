Bridgekeeper
-------------------------------

    | Who would cross the Bridge of Death
    | must answer me these questions three,
    | ere the other side he see.

    -- The Bridgekeeper, *Monty Python and the Holy Grail*

Bridgekeeper is a permissions library for `Django`_ projects. It's heavily inspired by `django-rules`_, but with one important difference: **it works on QuerySets as well as individual model instances**.

This means that you can efficiently show a :class:`~django.views.generic.list.ListView` of all of the model instances that your user is allowed to edit, for instance, without having your permission-checking code in two different places.

.. _django: https://djangoproject.com/
.. _django-rules: https://github.com/dfunckt/django-rules
