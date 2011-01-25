##############################################################################
#
# Copyright (c) 2010 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
from StringIO import StringIO
import httplib
import xmlrpclib

import transaction
from zope.app.appsetup.testlayer import ZODBLayer
from zope.app.wsgi import WSGIPublisherApplication
import wsgi_intercept
import zope.testbrowser.wsgi

# BBB
from zope.testbrowser.wsgi import Browser


class TransactionMiddleware(object):
    """This middleware makes the WSGI application compatible with the
    HTTPCaller behavior defined in zope.app.testing.functional:
    - It commits and synchronises the current transaction before and
      after the test.

    """
    def __init__(self, root_factory, wsgi_stack):
        # ZODBLayer creates DB in testSetUp method, but the middleware is
        # set up already in the `setUp` method, so we have only the
        # `root_factory` not the root itself:
        self.root_factory = root_factory
        self.wsgi_stack = wsgi_stack

    def __call__(self, environ, start_response):
        transaction.commit()
        for entry in self.wsgi_stack(environ, start_response):
            yield entry
        self.root_factory()._p_jar.sync()


class HandleErrorsMiddleware(object):
    """This middleware makes the WSGI application compatible with the
    HTTPCaller behavior defined in zope.app.testing.functional:
    - It honors the X-zope-handle-errors header in order to support
      zope.testbrowser Browser handleErrors flag.
    """

    default_handle_errors = 'True'

    def __init__(self, app, wsgi_stack):
        self.app = app
        self.wsgi_stack = wsgi_stack

    def __call__(self, environ, start_response):
        # Handle debug mode
        handle_errors = environ.get(
            'HTTP_X_ZOPE_HANDLE_ERRORS', self.default_handle_errors)
        self.app.handleErrors = handle_errors == 'True'

        for entry in self.wsgi_stack(environ, start_response):
            yield entry


class BrowserLayer(zope.testbrowser.wsgi.Layer, ZODBLayer):
    """This create a test layer with a test database and register a wsgi
    application to use that test database.

    A wsgi_intercept handler is installed as well, so you can use a
    WSGI version of zope.testbrowser Browser instance to access the
    application.
    """

    def setup_middleware(self, app):
        # Override this method in subclasses of this layer in order to set up
        # WSGI middleware.
        return app

    def make_wsgi_app(self):
        # Since the request factory class is only a parameter default of
        # WSGIPublisherApplication and not easily accessible otherwise, we fake
        # it into creating a requestFactory instance, so we can read the class
        # off of that in testSetUp()
        fake_db = object()
        self._application = WSGIPublisherApplication(fake_db)
        return HandleErrorsMiddleware(
            self._application,
            TransactionMiddleware(
                self.getRootFolder,
                self.setup_middleware(self._application)))

    def testSetUp(self):
        super(BrowserLayer, self).testSetUp()
        # Tell the publisher to use ZODBLayer's current database
        factory = type(self._application.requestFactory)
        self._application.requestFactory = factory(self.db)


class NotInBrowserLayer(Exception):
    """The current test is not running in a layer inheriting from
    BrowserLayer.
    """


class FakeResponse(object):
    """This behave like a Response object returned by HTTPCaller of
    zope.app.testing.functional.
    """

    def __init__(self, response_text):
        self.response_text = response_text

    def getStatus(self):
        line = self.getStatusString()
        status, rest = line.split(' ', 1)
        return int(status)

    def getStatusString(self):
        status_line = self.response_text.split('\n', 1)[0]
        protocol, status_string = status_line.split(' ', 1)
        return status_string

    def getHeader(self, name, default=None):
        without_body = self.response_text.split('\n\n', 1)[0]
        headers_text = without_body.split('\n', 1)[1]
        headers = headers_text.split('\n')
        result = []
        for header in headers:
            header_name, header_value = header.split(': ', 1)
            if name == header_name:
                result.append(header_value)
        if not result:
            return default
        elif len(result) == 1:
            return result[0]
        else:
            return result

    def getHeaders(self):
        without_body = self.response_text.split('\n\n', 1)[0]
        headers_text = without_body.split('\n', 1)[1]
        headers = headers_text.split('\n')
        result = []
        for header in headers:
            header_name, header_value = header.split(':', 1)
            result.append((header_name, header_value))
        return result

    def getBody(self):
        parts = self.response_text.split('\n\n', 1)
        if len(parts) < 2:
            return ''
        return parts[1]

    def getOutput(self):
        return self.response_text

    __str__ = getOutput

# XXX seems to only used by tests of zope.app.publication, maybe it should
# be moved there
def http(string, handle_errors=True):
    """This function behave like the HTTPCaller of
    zope.app.testing.functional.
    """
    key = ('localhost', 80)

    if key not in wsgi_intercept._wsgi_intercept:
        raise NotInBrowserLayer(NotInBrowserLayer.__doc__)

    (app_fn, script_name) = wsgi_intercept._wsgi_intercept[key]
    app = app_fn()

    if not string.endswith('\n'):
        string += '\n'
    string += 'X-zope-handle-errors: %s\n' % handle_errors

    socket = wsgi_intercept.wsgi_fake_socket(app, 'localhost', 80, '')
    socket.sendall(string.lstrip())
    result = socket.makefile()
    return FakeResponse(result.getvalue())


class FakeSocket(object):

    def __init__(self, data):
        self.data = data

    def makefile(self, mode, bufsize=None):
        return StringIO(self.data)


class XMLRPCTestTransport(xmlrpclib.Transport):
    """xmlrpclib transport that delegates to http().

    It can be used like a normal transport, including support for basic
    authentication.
    """

    verbose = False
    handleErrors = True

    def request(self, host, handler, request_body, verbose=0):
        request = "POST %s HTTP/1.0\n" % (handler,)
        request += "Content-Length: %i\n" % len(request_body)
        request += "Content-Type: text/xml\n"

        host, extra_headers, x509 = self.get_host_info(host)
        if extra_headers:
            request += "Authorization: %s\n" % (
                dict(extra_headers)["Authorization"],)

        request += "\n" + request_body
        response = http(request, handle_errors=self.handleErrors)

        errcode = response.getStatus()
        errmsg = response.getStatusString()
        # This is not the same way that the normal transport deals with the
        # headers.
        headers = response.getHeaders()

        if errcode != 200:
            raise xmlrpclib.ProtocolError(
                host + handler,
                errcode, errmsg,
                headers
                )

        res = httplib.HTTPResponse(FakeSocket(response.getBody()))
        res.begin()
        return self.parse_response(res)


def XMLRPCServerProxy(uri, transport=None, encoding=None,
                      verbose=0, allow_none=0, handleErrors=True):
    """A factory that creates a server proxy using the XMLRPCTestTransport
    by default.

    """
    if transport is None:
        transport = XMLRPCTestTransport()
    if isinstance(transport, XMLRPCTestTransport):
        transport.handleErrors = handleErrors
    return xmlrpclib.ServerProxy(uri, transport, encoding, verbose, allow_none)
