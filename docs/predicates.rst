Writing Predicates
==================

Ambient Predicates
------------------

We introduced what ambient predicates are, as well as how to write a custom one, in the :ref:`tutorial-ambient` section of the tutorial. There, we defined one predicate for each role, but if we had more than two roles that might get a bit repetitive.

If you need your ambient predicates to take arguments, the easiest way is to write a function that *returns* a predicate, like so:

.. code-block:: python
    :caption: shrubberies/predicates.py

    from bridgekeeper.predicates import ambient

    def has_role(role):

        def checker(user):
            return user.profile.role == role

        return ambient(checker, repr_string=f"has_role({role!r})")

In this case, we're using the optional ``repr_string`` argument to override how the predicate is displayed when debugging, so that we can see what the ``role`` argument is. (We're using `PEP 498`_ f-strings here, which are supported in Python 3.6+, but you don't have to.)

.. _PEP 498: https://www.python.org/dev/peps/pep-0498/
