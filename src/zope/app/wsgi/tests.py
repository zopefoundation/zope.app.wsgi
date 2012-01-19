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
from zope.app.wsgi.testing import SillyMiddleWareBrowserLayer
from zope.app.wsgi.testlayer import BrowserLayer
from zope.component.testlayer import ZCMLFileLayer
from zope.testing import renormalizing
import doctest
import re
import unittest
import zope.app.wsgi
import zope.event


def cleanEvents(s):
    zope.event.subscribers.pop()

def creating_app_w_paste_emits_ProcessStarting_event():
    """
    >>> import zope.event
    >>> events = []
    >>> subscriber = events.append
    >>> zope.event.subscribers.append(subscriber)

    >>> import os, tempfile
    >>> temp_dir = tempfile.mkdtemp()
    >>> sitezcml = os.path.join(temp_dir, 'site.zcml')
    >>> open(sitezcml, 'w').write('<configure />')
    >>> zopeconf = os.path.join(temp_dir, 'zope.conf')
    >>> open(zopeconf, 'w').write('''
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

def test_suite():

    checker = renormalizing.RENormalizing([
        (re.compile(
            r"&lt;class 'zope.component.interfaces.ComponentLookupError'&gt;"),
         r'ComponentLookupError'),
        ])
    filereturns_suite = doctest.DocFileSuite('filereturns.txt')
    filereturns_suite.layer = BrowserLayer(zope.app.wsgi)
    dt_suite = doctest.DocTestSuite()
    dt_suite.layer = BrowserLayer(zope.app.wsgi)

    readme_test = doctest.DocFileSuite(
            'README.txt',
            checker=checker, tearDown=cleanEvents,
            optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS)

    doctest_suite = doctest.DocFileSuite(
            'fileresult.txt', 'paste.txt',
            checker=checker,
            optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS)

    readme_test.layer = ZCMLFileLayer(zope.app.wsgi)
    doctest_suite.layer = ZCMLFileLayer(zope.app.wsgi)

    testlayer_suite = doctest.DocFileSuite(
            'testlayer.txt',
            optionflags=doctest.NORMALIZE_WHITESPACE)
    testlayer_suite.layer = SillyMiddleWareBrowserLayer(zope.app.wsgi)

    return unittest.TestSuite((
        filereturns_suite, readme_test, doctest_suite, testlayer_suite,
        dt_suite,
        ))
