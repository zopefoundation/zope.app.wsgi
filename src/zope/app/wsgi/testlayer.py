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
import base64
import http.client as httpclient
import re
import typing
import xmlrpc.client
from io import BytesIO

import transaction
import webtest
from webtest import TestRequest
from zope.app.appsetup.testlayer import ZODBLayer

from zope.app.wsgi import WSGIPublisherApplication


basicre = re.compile('Basic (.+)?:(.+)?$')
_TEST_APP_FOR_ENCODING = webtest.TestApp(None)


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
        plain = f'{u}:{p}'
        auth = base64.b64encode(plain.encode('utf-8'))
        return 'Basic %s' % str(auth.rstrip().decode('latin1'))
    return header


def is_wanted_header(header):
    """Return True if the given HTTP header key is wanted.
    """
    key, value = header
    return key.lower() not in ('x-content-type-warning', 'x-powered-by')


class TransactionMiddleware:
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
        yield from self.wsgi_stack(environ, start_response)
        self.root_factory()._p_jar.sync()


class AuthorizationMiddleware:
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

        yield from self.wsgi_stack(environ, application_start_response)


class BrowserLayer(ZODBLayer):
    """This create a test layer with a test database and register a wsgi
    application to use that test database.

    You can use a WSGI version of zope.testbrowser Browser instance to access
    the application.
    """
    allowTearDown = False

    def __init__(self, package, zcml_file='ftesting.zcml',
                 name=None, features=None, allowTearDown=False):
        super().__init__(package, zcml_file, name, features)
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
            super().tearDown()
        else:
            raise NotImplementedError


class NotInBrowserLayer(Exception):
    """The current test is not running in a layer inheriting from
    BrowserLayer.
    """


class FakeResponse:
    """This behave like a Response object returned by HTTPCaller of
    zope.app.testing.functional.
    """

    def __init__(self, response, request=None):
        self.response = response
        self.request = request

    @property
    def server_protocol(self):
        protocol = None
        if self.request is not None:
            protocol = self.request.environ.get('SERVER_PROTOCOL')
        if protocol is None:
            protocol = b'HTTP/1.0'
        if not isinstance(protocol, bytes):
            protocol = protocol.encode('latin1')
        return protocol

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

    def __bytes__(self):
        status = self.response.status
        if not isinstance(status, bytes):
            status = status.encode('latin1')
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

    getOutput = __bytes__

    def __str__(self):
        return bytes(self).decode('latin-1')


def encodeMultipartFormdata(
        fields: list[tuple[str, str]],
        files: typing.Optional[list] = None) -> tuple[bytes, bytes]:
    """Encode fields and files to be used in a multipart/form-data request.

    This function can be used in conjunction with `http()` (see below) to
    prepare the body of a POST request.

    Returns a tuple of content-type and content.
    """
    if files is None:
        files = []
    content_type, content = _TEST_APP_FOR_ENCODING.encode_multipart(
        fields, files)
    return content_type.encode(), content


def http(wsgi_app, string, handle_errors=True):
    request = TestRequest.from_file(BytesIO(string.lstrip()))
    request.environ['wsgi.handleErrors'] = handle_errors
    response = request.get_response(wsgi_app)
    return FakeResponse(response, request=request)


class FakeSocket:

    def __init__(self, data):
        self.data = data

    def makefile(self, mode, bufsize=None):
        return BytesIO(self.data)


class XMLRPCTestTransport(xmlrpc.client.Transport):
    """xmlrpc.client lib transport that delegates to http().

    It can be used like a normal transport, including support for basic
    authentication.
    """

    verbose = False
    handleErrors = True

    def request(self, host, handler, request_body, verbose=0):
        request = f"POST {handler} HTTP/1.0\n"
        request += "Content-Length: %i\n" % len(request_body)
        request += "Content-Type: text/xml\n"

        host, extra_headers, x509 = self.get_host_info(host)
        if extra_headers:
            request += "Authorization: {}\n".format(
                dict(extra_headers)["Authorization"])

        request += "\n" + request_body
        # XXX: http() needs to be passed a wsgi app!  where do we get a wsgi
        # app?
        response = http(request, handle_errors=self.handleErrors)

        errcode = response.getStatus()
        errmsg = response.getStatusString()
        # This is not the same way that the normal transport deals with the
        # headers.
        headers = response.getHeaders()

        if errcode != 200:
            raise xmlrpc.client.ProtocolError(
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
    return xmlrpc.client.ServerProxy(
        uri, transport, encoding, verbose, allow_none)
