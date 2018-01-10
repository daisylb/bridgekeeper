Bridgekeeper
-------------------------------

.. image:: https://img.shields.io/circleci/project/github/adambrenecki/bridgekeeper/master.svg
   :target: https://circleci.com/gh/adambrenecki/bridgekeeper
.. image:: https://img.shields.io/readthedocs/bridgekeeper.svg
   :target: https://bridgekeeper.readthedocs.io/
.. image:: https://img.shields.io/pypi/v/bridgekeeper.svg
   :target: https://pypi.python.org/pypi/bridgekeeper/
.. image:: https://img.shields.io/requires/github/adambrenecki/bridgekeeper.svg
   :target: https://requires.io/github/adambrenecki/bridgekeeper/requirements/?branch=master

    | Who would cross the Bridge of Death
    | must answer me these questions three,
    | ere the other side he see.

    -- The Bridgekeeper, *Monty Python and the Holy Grail*

Bridgekeeper is a permissions library for `Django`_ projects, where permissions are defined in your code, rather than in your database.

It's heavily inspired by `django-rules`_, but with one important difference: **it works on QuerySets as well as individual model instances**.

This means that you can efficiently show a :class:`~django.views.generic.list.ListView` of all of the model instances that your user is allowed to edit, for instance, without having your permission-checking code in two different places.

.. _django: https://djangoproject.com/
.. _django-rules: https://github.com/dfunckt/django-rules

Bridgekeeper works on Django 1.11 and 2.0 on Python 3.5+, and is licensed under the MIT License.

.. warning::

    Bridgekeeper (and these docs!) are a work in progress.
