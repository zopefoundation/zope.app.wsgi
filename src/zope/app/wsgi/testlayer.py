##############################################################################
#
# Copyright (c) 2010 Zope Corporation and Contributors.
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
import re
import base64
import httplib
import xmlrpclib

from transaction import commit
from wsgi_intercept.mechanize_intercept import Browser as BaseInterceptBrowser
from zope.app.appsetup.testlayer import ZODBLayer
from zope.app.publication.httpfactory import HTTPPublicationRequestFactory
from zope.app.wsgi import WSGIPublisherApplication
from zope.testbrowser.browser import Browser as ZopeTestbrowser
import wsgi_intercept

# List of hostname where the test browser/http function replies to
TEST_HOSTS = ['localhost', '127.0.0.1']


class InterceptBrowser(BaseInterceptBrowser):

    default_schemes = ['http']
    default_others = ['_http_error',
                      '_http_default_error']
    default_features = ['_redirect', '_cookies', '_referer', '_refresh',
                        '_equiv', '_basicauth', '_digestauth']


class Browser(ZopeTestbrowser):
    """Override the zope.testbrowser.browser.Browser interface so that it
    uses PatchedMechanizeBrowser
    """

    def __init__(self, *args, **kwargs):
        kwargs['mech_browser'] = InterceptBrowser()
        ZopeTestbrowser.__init__(self, *args, **kwargs)


# Compatibility helpers to behave like zope.app.testing

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
        auth = base64.encodestring('%s:%s' % (u, p))
        return 'Basic %s' % auth[:-1]
    return header


def is_wanted_header(header):
    """Return True if the given HTTP header key is unwanted.
    """
    key, value = header
    return key.lower() not in ('x-content-type-warning', 'x-powered-by')


class TestBrowserMiddleware(object):
    """This middleware makes the WSGI application compatible with the
    HTTPCaller behavior defined in zope.app.testing.functional:
    - It commits and synchronises the current transaction before and
      after the test.
    - It honors the X-zope-handle-errors header in order to support
      zope.testbrowser Browser handleErrors flag.
    - It modifies the HTTP Authorization header to encode user and
      password into base 64 if it is Basic authentication.
    """

    def __init__(self, app, root, handle_errors):
        assert isinstance(handle_errors, bool)
        self.root = root
        self.app = app
        self.default_handle_errors = str(handle_errors)

    def __call__(self, environ, start_response):
        # Handle debug mode
        handle_errors = environ.get(
            'HTTP_X_ZOPE_HANDLE_ERRORS', self.default_handle_errors)
        self.app.handleErrors = handle_errors == 'True'

        # Handle authorization
        auth_key = 'HTTP_AUTHORIZATION'
        if environ.has_key(auth_key):
            environ[auth_key] = auth_header(environ[auth_key])

        # Remove unwanted headers
        def application_start_response(status, headers):
            headers = filter(is_wanted_header, headers)
            start_response(status, headers)

        commit()
        for entry in self.app(environ, application_start_response):
            yield entry
        self.root._p_jar.sync()


class BrowserLayer(ZODBLayer):
    """This create a test layer with a test database and register a wsgi
    application to use that test database.

    A wsgi_intercept handler is installed as well, so you can use a
    WSGI version of zope.testbrowser Browser instance to access the
    application.
    """

    def testSetUp(self):
        super(BrowserLayer, self).testSetUp()
        wsgi_app = WSGIPublisherApplication(
            self.db, HTTPPublicationRequestFactory, True)

        def factory(handle_errors=True):
            return TestBrowserMiddleware(
                wsgi_app, self.getRootFolder(), handle_errors)

        for host in TEST_HOSTS:
            wsgi_intercept.add_wsgi_intercept(host, 80, factory)

    def testTearDown(self):
        for host in TEST_HOSTS:
            wsgi_intercept.remove_wsgi_intercept(host, 80)
        super(BrowserLayer, self).testTearDown()


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



def http(string, handle_errors=True):
    """This function behave like the HTTPCaller of
    zope.app.testing.functional.
    """
    key = ('localhost', 80)

    if key not in wsgi_intercept._wsgi_intercept:
        raise NotInBrowserLayer(NotInBrowserLayer.__doc__)

    (app_fn, script_name) = wsgi_intercept._wsgi_intercept[key]
    app = app_fn(handle_errors=handle_errors)

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
