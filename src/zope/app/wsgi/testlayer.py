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

import transaction
from zope.app.appsetup.testlayer import ZODBLayer
from zope.app.wsgi import WSGIPublisherApplication
from zope.testbrowser.wsgi import Layer as WSGILayer, AuthorizationMiddleware
from webtest import TestRequest

# BBB
#from zope.testbrowser.wsgi import Browser

from zope.app.wsgi._compat import httpclient, xmlrpcclient


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


class BrowserLayer(WSGILayer, ZODBLayer):
    """This create a test layer with a test database and register a wsgi
    application to use that test database.

    You can use a WSGI version of zope.testbrowser Browser instance to access
    the application.
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
        return AuthorizationMiddleware(
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
        parts = [b'HTTP/1.0 ' + self.response.status.encode('latin1')]
        parts += [('%s: %s' % h).encode('latin1') for h in self.getHeaders()]

        body = self.response.body
        if body:
            if not isinstance(body, bytes):
                body = body.encode('utf-8')
            parts += [b'', body]
        return b'\n'.join(parts)

    def __str__(self):
        out = self.getOutput()
        return out.decode('latin1')

def http(string, handle_errors=True):
    app = WSGILayer.get_app()
    if app is None:
        raise NotInBrowserLayer(NotInBrowserLayer.__doc__)

    request = TestRequest.from_file(BytesIO(string))
    request.environ['wsgi.handleErrors'] = handle_errors
    response = request.get_response(app)
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
