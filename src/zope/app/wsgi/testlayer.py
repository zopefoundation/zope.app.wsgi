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

import wsgi_intercept
from zope.app.appsetup.testlayer import ZODBLayer

from zope.app.wsgi import WSGIPublisherApplication
from zope.app.publication.httpfactory import HTTPPublicationRequestFactory
from wsgi_intercept.mechanize_intercept import Browser as BaseInterceptBrowser
from zope.testbrowser.browser import Browser as ZopeTestbrowser

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


class BrowserLayer(ZODBLayer):
    """This create a test layer with a test database and register a wsgi
    application to use that test database.

    A wsgi_intercept handler is installed as well, so you can use a
    WSGI version of zope.testbrowser Browser instance to access the
    application.
    """

    handleErrors = True

    def testSetUp(self):
        super(BrowserLayer, self).testSetUp()
        wsgi_app = WSGIPublisherApplication(
            self.db, HTTPPublicationRequestFactory, self.handleErrors)

        def factory():
            return wsgi_app

        wsgi_intercept.add_wsgi_intercept('localhost', 80, factory)


    def testTearDown(self):
        super(BrowserLayer, self).testTearDown()
        wsgi_intercept.remove_wsgi_intercept('localhost', 80)


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

