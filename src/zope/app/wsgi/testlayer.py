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
    default_others = ['_http_error', '_http_request_upgrade',
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

    def __init__(self, app, root):
        self.root = root
        self.app = app

    def __call__(self, environ, start_response):
        handle_errors = environ.get('HTTP_X_ZOPE_HANDLE_ERRORS', 'True')
        self.app.handleErrors = handle_errors == 'True'

        auth_key = 'HTTP_AUTHORIZATION'
        if environ.has_key(auth_key):
            environ[auth_key] = auth_header(environ[auth_key])

        commit()
        for entry in self.app(environ, start_response):
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

        def factory():
            return TestBrowserMiddleware(wsgi_app, self.getRootFolder())

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


def http(string):
    key = ('localhost', 80)

    if key not in wsgi_intercept._wsgi_intercept:
        raise NotInBrowserLayer(NotInBrowserLayer.__doc__)

    (app_fn, script_name) = wsgi_intercept._wsgi_intercept[key]
    app = app_fn()

    socket = wsgi_intercept.wsgi_fake_socket(app, 'localhost', 80, '')
    socket.sendall(string.lstrip())
    result = socket.makefile()
    return result.getvalue()

