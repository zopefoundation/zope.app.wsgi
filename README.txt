=====================
Zope WSGI Application
=====================

This package contains an interpretation of the WSGI specification (PEP-0333)
for the Zope application server by providing a WSGI application object. First,
we create a stream that will contain the response:

  >>> import StringIO
  >>> data = StringIO.StringIO('')

Usually this stream is created by the HTTP server and refers to the output
stream sent to the server client.

Now that we have our output stream, we need to initialize the WSGI-compliant
Zope application that is called from the server. To do that, we first have to
create and open a ZODB connection:

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

Even though this is commonly done by the server, our first task is to create
an appropriate environment for the request.

  >>> environ = {
  ...     'PATH_INFO': '/',
  ...     'wsgi.input': StringIO.StringIO('')}

Next we create a WSGI-compliant ``start_response()`` method that accepts the
status of the response to the HTTP request and the headers that are part of
the response stream. The headers are expected to be a list of
2-tuples. However, for the purpose of this demonstration we simply ignore all
the arguments and push a simple message to the stream. The
``start_response()`` funtion must also return a ``write()`` callable that
accepts further data.

  >>> def start_response(status, headers):
  ...     data.write('status and headers.\n\n')
  ...     return data.write
  ...

Now we can send the fabricated HTTP request to the application for processing:

  >>> app(environ, start_response)
  ''

We expect the output of this call to be always an empty string, since all the
output is written to the output stream directly. Looking at the output 

  >>> print data.getvalue()
  status and headers.
  <BLANKLINE>
  <html><head><title>Unauthorized</title></head>
  <body><h2>Unauthorized</h2>
  A server error occurred.
  </body></html>
  <BLANKLINE>

we can see that application really crashed and did not know what to do. This
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


The ``IWSGIOutput`` Component
-----------------------------

Under the hood the WSGI support uses a component that implements
``IWSGIOutput`` that manages the response headers and provides the output
stream by implementing the ``write()`` method. In the following text the
functionality of this class is introduced:  

First, we reset our output stream:

  >>> data.__init__('')

Then we initialize an instance of the WSGI output object:

  >>> output = wsgi.WSGIOutput(start_response)

You can set the response status

  >>> output.setResponseStatus("200", "OK")
  >>> output._statusString
  '200 OK'

or set arbitrary headers as a mapping:

  >>> output.setResponseHeaders({'a':'b', 'c':'d'})

The headers must be returned as a list of tuples:

  >>> output.getHeaders()
  [('a', 'b'), ('c', 'd')]
  
Calling ``setResponseHeaders()`` again adds new values:

  >>> output.setResponseHeaders({'x':'y', 'c':'d'})
  >>> h = output.getHeaders()
  >>> h.sort()
  >>> h
  [('a', 'b'), ('c', 'd'), ('x', 'y')]

Headers that can potentially repeat are added using
``appendResponseHeaders()``:

  >>> output.appendResponseHeaders(['foo: bar'])
  >>> h = output.getHeaders()
  >>> h.sort()
  >>> h    
  [('a', 'b'), ('c', 'd'), ('foo', ' bar'), ('x', 'y')]
  >>> output.appendResponseHeaders(['foo: bar'])
  >>> h = output.getHeaders()
  >>> h.sort()
  >>> h    
  [('a', 'b'), ('c', 'd'), ('foo', ' bar'), ('foo', ' bar'), ('x', 'y')]

Headers containing a colon should also work

  >>> output.appendResponseHeaders(['my: brain:hurts'])
  >>> h = output.getHeaders()
  >>> h.sort()
  >>> h
  [('a', 'b'), ('c', 'd'), ('foo', ' bar'), ('foo', ' bar'), 
   ('my', ' brain:hurts'), ('x', 'y')]

The headers should not be written to the output

  >>> output.wroteResponseHeader()
  False
  >>> data.getvalue()
  ''

Let's now write something to the output stream:

  >>> output.write('Now for something')

The headers should be sent and the data written to the stream:

  >>> output.wroteResponseHeader()
  True
  >>> data.getvalue()
  'status and headers.\n\nNow for something'

Calling write again the headers should not be sent again

  >>> output.write(' completly different!')
  >>> data.getvalue()
  'status and headers.\n\nNow for something completly different!'


About WSGI
----------

WSGI is the Python Web Server Gateway Interface, an upcoming PEP to
standardize the interface between web servers and python applications to
promote portability.

For more information, refer to the WSGI specification:
http://www.python.org/peps/pep-0333.html

