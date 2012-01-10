=====================
Zope WSGI Application
=====================

This package contains an interpretation of the WSGI specification (PEP-0333)
for the Zope application server by providing a WSGI application object. The
first step is to initialize the WSGI-compliant Zope application that is called
from the server. To do that, we first have to create and open a ZODB
connection:

  >>> from ZODB.MappingStorage import MappingStorage
  >>> from ZODB.DB import DB

  >>> storage = MappingStorage('test.db')
  >>> db = DB(storage, cache_size=4000)

We can now initialize the application:

  >>> from zope.app import wsgi
  >>> app = wsgi.WSGIPublisherApplication(db)

The callable ``app`` object accepts two positional arguments, the environment
and the function that initializes the response and returns a function with
which the output data can be written.

Even though this is commonly done by the server, we now have to create an
appropriate environment for the request.

  >>> import cStringIO
  >>> environ = {
  ...     'PATH_INFO': '/',
  ...     'wsgi.input': cStringIO.StringIO('')}

Next we create a WSGI-compliant ``start_response()`` method that accepts the
status of the response to the HTTP request and the headers that are part of
the response stream. The headers are expected to be a list of 2-tuples. The
``start_response()`` method must also return a ``write()`` function that
directly writes the output to the server. However, the Zope 3 implementation
will not utilize this function, since it is strongly discouraged by
PEP-0333. The second method of getting data to the server is by returning an
iteratable from the application call. Sp we simply ignore all the arguments
and return ``None`` as the write method.

  >>> def start_response(status, headers):
  ...     return None

Now we can send the fabricated HTTP request to the application for processing:

  >>> print ''.join(app(environ, start_response))
  <html><head><title>SystemError</title></head>
  <body><h2>SystemError</h2>
  A server error occurred.
  </body></html>
  <BLANKLINE>

We can see that application really crashed and did not know what to do. This
is okay, since we have not setup anything. Getting a request successfully
processed would require us to bring up a lot of Zope 3's system, which would
be just a little bit too much for this demonstration.

Now that we have seen the manual way of initializing and using the publisher
application, here is the way it is done using all of Zope 3's setup machinery::

    from zope.app.server.main import setup, load_options
    from zope.app.wsgi import PublisherApp

    # Read all configuration files and bring up the component architecture
    args = ["-C/path/to/zope.conf"]
    db = setup(load_options(args))

    # Initialize the WSGI-compliant publisher application with the database
    wsgiApplication = PublisherApp(db)

    # Here is an example on how the application could be registered with a
    # WSGI-compliant server. Note that the ``setApplication()`` method is not
    # part of the PEP 333 specification.
    wsgiServer.setApplication(wsgiApplication)

The code above assumes, that Zope is available on the ``PYTHONPATH``.  Note
that you may have to edit ``zope.conf`` to provide an absolute path for
``site.zcml``. Unfortunately we do not have enough information about the
directory structure to make this code a doctest.

In summary, to use Zope as a WSGI application, the following steps must be
taken:

* configure and setup Zope

* an instance of ``zope.app.wsgi.PublisherApp`` must be created with a
  refernce to the opened database

* this application instance must be somehow communicated to the WSGI server,
  i.e. by calling a method on the server that sets the application.


Access logging
--------------

But let's test at least the user info logging feature. We can check the
environ after being sent to the app and also see that a key has been set to
store user names for use in access logs.

This logging information is provided by an adapter registered for
`ILoggingInfo`. Out-of-the-box, `zope.publisher` registers a base
adapter that returns the principal id as value::

  >>> from pprint import pprint
  >>> pprint(environ)
  {'PATH_INFO': '/',
   'REMOTE_USER': 'zope.anybody',
   'wsgi.input': <cStringIO.StringI object at ...>,
   'wsgi.logging_info': 'zope.anybody'}

.. edge case

   If remote user is already set, don't update it:

    >>> environ = {
    ...     'PATH_INFO': '/',
    ...     'REMOTE_USER': 'someoneelse',
    ...     'wsgi.input': cStringIO.StringIO('')}

    >>> _ = list(app(environ, start_response))
    >>> pprint(environ)
    {'PATH_INFO': '/',
     'REMOTE_USER': 'someoneelse',
     'wsgi.input': <cStringIO.StringI object at ...>,
     'wsgi.logging_info': 'zope.anybody'}


Creating A WSGI Application
---------------------------

We do not always want Zope to control the startup process. People want to be
able to start their favorite server and then register Zope simply as a WSGI
application. For those cases we provide a very high-level function called
``getWSGIApplication()`` that only requires the configuration file to set up
the Zope 3 application server and returns a WSGI application. Here is a simple
example:

  # We have to create our own site definition file -- which will simply be
  # empty -- to provide a minimal test.
  >>> import os, tempfile
  >>> temp_dir = tempfile.mkdtemp()
  >>> sitezcml = os.path.join(temp_dir, 'site.zcml')
  >>> open(sitezcml, 'w').write('<configure />')

  >>> from cStringIO import StringIO
  >>> configFile = StringIO('''
  ... site-definition %s
  ...
  ... <zodb>
  ...   <mappingstorage />
  ... </zodb>
  ...
  ... <eventlog>
  ...   <logfile>
  ...     path STDOUT
  ...   </logfile>
  ... </eventlog>
  ...
  ... <product-config sample>
  ...   key1 val1
  ... </product-config>
  ... ''' %sitezcml)


Create an handler for the event.

  >>> import zope.component
  >>> from zope.app.wsgi.interfaces import IWSGIPublisherApplicationCreatedEvent
  >>> called = []

  >>> @zope.component.adapter(IWSGIPublisherApplicationCreatedEvent)
  ... def handler(event):
  ...     called.append(event)

  >>> zope.component.provideHandler(handler)

Create an WSGI application.

  >>> app = wsgi.getWSGIApplication(configFile)
  >>> app
  <zope.app.wsgi.WSGIPublisherApplication object at ...>

  >>> called[0].application is app
  True

The product configs were parsed:

  >>> import zope.app.appsetup.product as zapp
  >>> print zapp.getProductConfiguration('sample')
  {'key1': 'val1'}

  >>> import shutil
  >>> shutil.rmtree(temp_dir)


About WSGI
----------

WSGI is the Python Web Server Gateway Interface, a PEP to standardize
the interface between web servers and python applications to promote
portability.

For more information, refer to the WSGI specification:
http://www.python.org/peps/pep-0333.html

