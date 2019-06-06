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
from io import BytesIO

import base64
import re
import transaction
from zope.app.appsetup.testlayer import ZODBLayer
from zope.app.wsgi import WSGIPublisherApplication
from webtest import TestRequest

from zope.app.wsgi._compat import httpclient, xmlrpcclient

basicre = re.compile('Basic (.+)?:(.+)?$')

def auth_header(header):
    """This function takes an authorization HTTP header and encode the
    couple user, password into base 64 like the HTTP protocol wants
    it.
    """
    match = basicre.match(header)
    if match:
        u, p = match.group(1, 2)
        if u is None:
            u = ''
        if p is None:
            p = ''
        plain = '%s:%s' % (u, p)
        auth = base64.b64encode(plain.encode('utf-8'))
        return 'Basic %s' % str(auth.rstrip().decode('latin1'))
    return header


def is_wanted_header(header):
    """Return True if the given HTTP header key is wanted.
    """
    key, value = header
    return key.lower() not in ('x-content-type-warning', 'x-powered-by')


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


class AuthorizationMiddleware(object):
    """This middleware makes the WSGI application compatible with the
    HTTPCaller behavior defined in zope.app.testing.functional:
    - It modifies the HTTP Authorization header to encode user and
      password into base64 if it is Basic authentication.
    """

    def __init__(self, wsgi_stack):
        self.wsgi_stack = wsgi_stack

    def __call__(self, environ, start_response):
        # Handle authorization
        auth_key = 'HTTP_AUTHORIZATION'
        if auth_key in environ:
            environ[auth_key] = auth_header(environ[auth_key])

        # Remove unwanted headers
        def application_start_response(status, headers, exc_info=None):
            headers = list(filter(is_wanted_header, headers))
            start_response(status, headers)

        for entry in self.wsgi_stack(environ, application_start_response):
            yield entry


class BrowserLayer(ZODBLayer):
    """This create a test layer with a test database and register a wsgi
    application to use that test database.

    You can use a WSGI version of zope.testbrowser Browser instance to access
    the application.
    """
    allowTearDown = False

    def __init__(self, package, zcml_file='ftesting.zcml',
                 name=None, features=None, allowTearDown=False):
        super(BrowserLayer, self).__init__(package, zcml_file, name, features)
        self.allowTearDown = allowTearDown

    def setup_middleware(self, app):
        # Override this method in subclasses of this layer in order to set up
        # WSGI middleware.
        return app

    def make_wsgi_app(self, setup_middleware=lambda a: a):
        self._application = WSGIPublisherApplication(self.db)
        return AuthorizationMiddleware(
            TransactionMiddleware(
                self.getRootFolder,
                self.setup_middleware(
                    setup_middleware(self._application)
                    )
                )
            )

    def tearDown(self):
        if self.allowTearDown:
            super(BrowserLayer, self).tearDown()
        else:
            raise NotImplementedError

class NotInBrowserLayer(Exception):
    """The current test is not running in a layer inheriting from
    BrowserLayer.
    """


class FakeResponse(object):
    """This behave like a Response object returned by HTTPCaller of
    zope.app.testing.functional.

    .. versionchanged:: 4.1.0
       Implement support for unicode() on Python 2 to be equivalent to
       str() on Python 3, and implement support for bytes() on Python 3
       to be equivalent to str() on Python 2. This should help in cross version
       testing.

       On Python 2, ``getOutput`` and ``__str__`` should no longer produce
       UnicodeErrors.

    """

    # XXX: zope.app.testing.functional used to respond with HTTP/1.1
    server_protocol = b'HTTP/1.0'

    def __init__(self, response):
        self.response = response

    def getStatus(self):
        return self.response.status_int

    def getStatusString(self):
        return self.response.status

    def getHeader(self, name, default=None):
        return self.response.headers.get(name, default)

    def getHeaders(self):
        return sorted(self.response.headerlist)

    def getBody(self):
        return self.response.body

    def getOutput(self):
        status = self.response.status
        status = status.encode('latin1') if not isinstance(status, bytes) else status
        parts = [self.server_protocol + b' ' + status]

        headers = [(k.encode('latin1') if not isinstance(k, bytes) else k,
                    v.encode('latin1') if not isinstance(v, bytes) else v)
                   for k, v in self.getHeaders()]

        parts += [k + b': ' + v for k, v in headers]

        body = self.response.body
        if body:
            if not isinstance(body, bytes):
                body = body.encode('utf-8')
            parts += [b'', body]
        return b'\n'.join(parts)

    if str is bytes: # Py2

        # Forcing __str__ through latin1, as Py3 does, will return
        # unicode which will then be decoded as ascii, which could
        # cause an UnicodeError.
        __str__ = getOutput

        def __unicode__(self):
            return self.getOutput().decode('latin-1')
    else:
        __bytes__ = getOutput

        def __str__(self):
            return self.getOutput().decode('latin-1')


def http(wsgi_app, string, handle_errors=True):
    request = TestRequest.from_file(BytesIO(string.lstrip()))
    request.environ['wsgi.handleErrors'] = handle_errors
    response = request.get_response(wsgi_app)
    return FakeResponse(response)


class FakeSocket(object):

    def __init__(self, data):
        self.data = data

    def makefile(self, mode, bufsize=None):
        return BytesIO(self.data)


class XMLRPCTestTransport(xmlrpcclient.Transport):
    """xmlrpc.client lib transport that delegates to http().

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
        # XXX: http() needs to be passed a wsgi app!  where do we get a wsgi app?
        response = http(request, handle_errors=self.handleErrors)

        errcode = response.getStatus()
        errmsg = response.getStatusString()
        # This is not the same way that the normal transport deals with the
        # headers.
        headers = response.getHeaders()

        if errcode != 200:
            raise xmlrpcclient.ProtocolError(
                host + handler,
                errcode, errmsg,
                headers
                )

        res = httpclient.HTTPResponse(FakeSocket(response.getBody()))
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
    return xmlrpcclient.ServerProxy(uri, transport, encoding, verbose, allow_none)
