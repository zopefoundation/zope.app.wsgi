##############################################################################
#
# Copyright (c) 2004 Zope Foundation and Contributors.
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
"""WSGI tests"""
import doctest
import io
import re
import unittest

from zope.app.wsgi.testing import SillyMiddleWare
from zope.app.wsgi.testlayer import BrowserLayer
from zope.authentication.interfaces import IUnauthenticatedPrincipal
from zope.component.testlayer import ZCMLFileLayer
from zope.publisher.interfaces.logginginfo import ILoggingInfo
from zope.testing import renormalizing
import zope.app.wsgi
import zope.component
import zope.component.testing
import zope.event
import zope.interface


def creating_app_w_paste_emits_ProcessStarting_event():
    """
    >>> import zope.event
    >>> events = []
    >>> subscriber = events.append
    >>> zope.event.subscribers.append(subscriber)

    >>> import os, tempfile
    >>> temp_dir = tempfile.mkdtemp()
    >>> sitezcml = os.path.join(temp_dir, 'site.zcml')
    >>> written = open(sitezcml, 'w').write('<configure />')
    >>> zopeconf = os.path.join(temp_dir, 'zope.conf')
    >>> wrotten = open(zopeconf, 'w').write('''
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
    ... ''' % sitezcml)

    >>> import zope.app.wsgi.paste, zope.processlifetime
    >>> app = zope.app.wsgi.paste.ZopeApplication(
    ...     {}, zopeconf, handle_errors=False)

    >>> len([e for e in events
    ...     if isinstance(e, zope.processlifetime.ProcessStarting)]) == 1
    True

    >>> zope.event.subscribers.remove(subscriber)
    """


wsgiapp_layer = BrowserLayer(zope.app.wsgi, name='wsgiapp', allowTearDown=True)


def setUpWSGIApp(test):
    test.globs['wsgi_app'] = wsgiapp_layer.make_wsgi_app()


def setUpSillyWSGIApp(test):
    test.globs['wsgi_app'] = wsgiapp_layer.make_wsgi_app(SillyMiddleWare)


@zope.component.adapter(IUnauthenticatedPrincipal)
@zope.interface.implementer(ILoggingInfo)
def could_not_adapt_principal_to_logging_info(context):
    """Fake that a principal could not be adapted to ILoggingInfo."""
    return None


class WSGIPublisherApplicationTests(unittest.TestCase):
    """Testing .WSGIPublisherApplication."""

    layer = wsgiapp_layer

    def setUp(self):
        zope.component.provideAdapter(
            could_not_adapt_principal_to_logging_info)

    def tearDown(self):
        super(WSGIPublisherApplicationTests, self).tearDown()
        gsm = zope.component.getGlobalSiteManager()
        assert gsm.unregisterAdapter(could_not_adapt_principal_to_logging_info)

    def test_WSGIPublisherApplication___call___1(self):
        """It sets '-' as 'wsgi.logging_info' in environ as fall back.

        This is the case if the principal couldn't be adapted to ILoggingInfo.
        """
        from . import WSGIPublisherApplication

        app = WSGIPublisherApplication()
        environ = {'wsgi.input': io.BytesIO(b'')}
        list(app(environ, lambda status, headers: None))
        self.assertEqual('-', environ['wsgi.logging_info'])


def test_suite():
    suites = []
    checker = renormalizing.RENormalizing([
        (re.compile(
            r"&lt;class 'zope.component.interfaces.ComponentLookupError'&gt;"),
         r'ComponentLookupError'),
    ])

    filereturns_suite = doctest.DocFileSuite(
        'filereturns.txt', setUp=setUpWSGIApp)
    filereturns_suite.layer = wsgiapp_layer
    suites.append(filereturns_suite)

    dt_suite = doctest.DocTestSuite()
    dt_suite.layer = wsgiapp_layer
    suites.append(dt_suite)

    suites.append(unittest.makeSuite(WSGIPublisherApplicationTests))

    readme_test = doctest.DocFileSuite(
        'README.txt',
        checker=checker,
        optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS)
    # This test needs its own layer/teardown, since it registers components
    # with objects that later do not exist.
    readme_test.layer = ZCMLFileLayer(zope.app.wsgi, name="README")
    suites.append(readme_test)

    doctest_suite = doctest.DocFileSuite(
        'fileresult.txt', 'paste.txt',
        checker=checker,
        optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS)
    doctest_suite.layer = ZCMLFileLayer(zope.app.wsgi)
    suites.append(doctest_suite)

    testlayer_suite = doctest.DocFileSuite(
        'testlayer.txt', setUp=setUpSillyWSGIApp,
        optionflags=doctest.NORMALIZE_WHITESPACE)
    testlayer_suite.layer = wsgiapp_layer
    suites.append(testlayer_suite)

    return unittest.TestSuite(suites)
