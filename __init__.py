##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
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
"""A WSGI Application wrapper for zope

$Id$
"""
from zope.interface import implements
from zope.publisher.publish import publish
from zope.publisher.interfaces.http import IHeaderOutput

from zope.app.publication.httpfactory import HTTPPublicationRequestFactory
from zope.app.wsgi import interfaces


class WSGIPublisherApplication(object):
    """A WSGI application implemenation for the zope publisher

    Instances of this class can be used as a WSGI application object.

    The class relies on a properly initialized request factory.
    """
    implements(interfaces.IWSGIApplication)

    def __init__(self, db=None, factory=HTTPPublicationRequestFactory):
        self.requestFactory = None

        if db is not None:
            self.requestFactory = factory(db)

    def __call__(self, environ, start_response):
        """See zope.app.wsgi.interfaces.IWSGIApplication"""
        request = self.requestFactory(environ['wsgi.input'], environ)

        # Let's support post-mortem debugging
        handle_errors = environ.get('wsgi.handleErrors', True)

        request = publish(request, handle_errors=handle_errors)
        response = request.response

        # Start the WSGI server response
        start_response(response.getStatusString(), response.getHeaders())

        # Return the result body iterable.
        return response.consumeBodyIter()
