This package provides the ``WSGIPublisherApplication`` class which
exposes the object publishing machinery in ``zope.publisher`` as a
WSGI application.  It also lets us bring up the Zope application
server (parsing ``zope.conf`` and ``site.zcml``) with a mere function
call::

    >>> db = zope.app.wsgi.config('zope.conf')

This is especially useful for debugging.

To bring up Zope and obtain the WSGI application object at the same
time, use the ``getWSGIApplication`` function.

This package also provides an easy to use application factory for
PasteDeploy_. You can simply specify an application configuration
like this in your Paste configuration file::

    [app:main]
    use = egg:zope.app.wsgi
    config_file = %(here)s/zope.conf

Look for more documentation inside the package itself.

.. _PasteDeploy: http://pythonpaste.org/deploy/
