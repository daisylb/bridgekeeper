Contribution guide
==================

.. todo::

    write this

Publishing a release
-----

The process for releasing looks something like this:

.. code-block:: sh

    poetry version minor
    nox -s release_test
    git add .
    git commit -m "Release 1.1"
    git tag v1.1
    git push origin develop v1.1
    poetry publish

Then `draft a new release <https://github.com/excitedleigh/bridgekeeper/releases/new>`_ to trigger the documentation build.
