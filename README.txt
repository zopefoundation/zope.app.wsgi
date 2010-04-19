This package provides the ``WSGIPublisherApplication`` class which
exposes the object publishing machinery in ``zope.publisher`` as a
WSGI application.  It also lets us bring up the Zope application
server (parsing ``zope.conf`` and ``site.zcml``) with a mere function
call::

    >>> db = zope.app.wsgi.config('zope.conf')

This is especially useful for debugging.

To bring up Zope and obtain the WSGI application object at the same
time, use the ``getWSGIApplication`` function.  Here's an example of a
factory a la PasteDeploy_::

    def application_factory(global_conf):
        zope_conf = os.path.join(global_conf['here'], 'zope.conf')
        return zope.app.wsgi.getWSGIApplication(zope_conf)

.. _PasteDeploy: http://pythonpaste.org/deploy/


Changes
=======

3.4.3 (2010-04-19)
------------------

* Bugfix: initialize any <logger> defined in the config, as zope.app.server does

3.4.2 (2009-09-10)
------------------

* Support product configuration sections in Zope configuration files.

3.4.1 (2008-07-30)
------------------

* Added Trove classifiers.

* Notify WSGIPublisherApplicationCreated event when WSGI application is
  created.

* Fixed deprecation warning in ftesting.zcml: ZopeSecurityPolicy moved to
  zope.securitypolicy.

3.4.0 (2007-09-14)
------------------

* Fixed the tests to run on Python 2.5 as well as Python 2.4.

* Split ``getApplication`` into ``config`` and ``getApplication`` so
  that ``config`` could be reused, for example for debugging.

3.4.0a1 (2007-04-22)
--------------------

Initial release as a separate project, corresponds to zope.app.wsgi
from Zope 3.4.0a1
