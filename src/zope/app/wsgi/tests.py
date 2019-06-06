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
    >>> with open(sitezcml, 'w') as f:
    ...     _ = f.write('<configure />')
    >>> zopeconf = os.path.join(temp_dir, 'zope.conf')
    >>> with open(zopeconf, 'w') as f:
    ...     _ = f.write('''
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


class AuthHeaderTestCase(unittest.TestCase):

    def test_auth_encoded(self):
        from zope.app.wsgi.testlayer import auth_header
        header = 'Basic Z2xvYmFsbWdyOmdsb2JhbG1ncnB3'
        self.assertEqual(auth_header(header), header)

    def test_auth_non_encoded(self):
        from zope.app.wsgi.testlayer import auth_header
        header = 'Basic globalmgr:globalmgrpw'
        expected = 'Basic Z2xvYmFsbWdyOmdsb2JhbG1ncnB3'
        self.assertEqual(auth_header(header), expected)

    def test_auth_non_encoded_empty(self):
        from zope.app.wsgi.testlayer import auth_header
        header = 'Basic globalmgr:'
        expected = 'Basic Z2xvYmFsbWdyOg=='
        self.assertEqual(auth_header(header), expected)
        header = 'Basic :pass'
        expected = 'Basic OnBhc3M='
        self.assertEqual(auth_header(header), expected)

    def test_auth_non_encoded_colon(self):
        from zope.app.wsgi.testlayer import auth_header
        header = 'Basic globalmgr:pass:pass'
        expected = 'Basic Z2xvYmFsbWdyOnBhc3M6cGFzcw=='
        self.assertEqual(auth_header(header), expected)


class TestFakeResponse(unittest.TestCase):

    def test_doesnt_assume_encoding_of_headers(self):
        # https://github.com/zopefoundation/zope.app.wsgi/issues/7
        # headers on Py2 should already be bytes or at least be allowed
        # to be bytes. For BWC, we allow them to be bytes or unicode either
        # platform.
        # The body/__str__ can be decoded correctly too when this happens
        from zope.app.wsgi.testlayer import FakeResponse

        try:
            text_type = unicode
        except NameError:
            text_type = str
        class MockResponse(object):

            status = '200 OK'
            body = ''

            def __init__(self):
                self.headerlist = []

        response = MockResponse()
        # A latin-1 byte.
        response.headerlist.append(("X-Header".encode('latin-1'),
                                    u"voill\xe0".encode('latin-1')))

        fake = FakeResponse(response)
        self.assertEqual(fake.getOutput(), b'HTTP/1.0 200 OK\nX-Header: voill\xe0')
        # No matter the platform, str/bytes should not raise
        self.assertIn('HTTP', str(fake))
        self.assertIn(b'HTTP', bytes(fake))
        self.assertEqual(text_type(fake),
                         u'HTTP/1.0 200 OK\nX-Header: voill\xe0')

        # A utf-8 byte, smuggled inside latin-1, as discussed in PEP3333
        response.headerlist[0] = (b'X-Header',
                                  u'p-o-p \U0001F4A9'.encode('utf-8').decode('latin-1'))
        self.assertEqual(fake.getOutput(),
                         b'HTTP/1.0 200 OK\nX-Header: p-o-p \xf0\x9f\x92\xa9')
        self.assertIn('HTTP', str(fake))
        self.assertIn(b'HTTP', bytes(fake))
        self.assertEqual(text_type(fake),
                         u'HTTP/1.0 200 OK\nX-Header: p-o-p \xf0\x9f\x92\xa9')

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

    suites.append(unittest.defaultTestLoader.loadTestsFromName(__name__))

    return unittest.TestSuite(suites)
