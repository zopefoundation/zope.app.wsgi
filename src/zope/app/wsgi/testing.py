##############################################################################
#
# Copyright (c) 2007 Zope Foundation and Contributors.
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
"""zope.app.wsgi common test related classes/functions/objects.
"""
import tempfile

from zope import interface, component
import zope.publisher.interfaces.browser

from zope.app.wsgi.testlayer import BrowserLayer


@interface.implementer(zope.publisher.interfaces.browser.IBrowserPublisher)
@component.adapter(
    interface.Interface, zope.publisher.interfaces.browser.IBrowserRequest)
class FileView:

    def __init__(self, _, request):
        self.request = request

    def browserDefault(self, *_):
        return self, ()

    def __call__(self):
        self.request.response.setHeader('content-type', 'text/plain')
        fn = tempfile.mktemp()
        with open(fn, 'wb') as file:
            file.write(b"Hello\nWorld!\n")
        file = open(fn, 'rb')
        return file


class IndexView(FileView):
    def __call__(self):
        self.request.response.setHeader('content-type', 'text/html')
        return '''
            <html>
              <head>
              </head>
              <body>
                <p>This is the index</p>
              </body>
            </html>'''

class ErrorRaisingView(FileView):
    def __call__(self):
        return 1/0

class SillyMiddleWare(object):
    def __init__(self, application):
        self.application = application

    def __call__(self, environ, start_response):
        def drop_content_length_response(status, headers, exc_info=None):
            for name, value in headers:
                if name.lower() == 'content-length':
                    headers.remove((name, value))
            return start_response(status, headers, exc_info=exc_info)

        app_iter = self.application(environ, drop_content_length_response)

        # Very silly indeed:
        result = b''.join(app_iter)
        return [result.replace(
            b'<body>', b'<body><h1>Hello from the silly middleware</h1>')]


class SillyMiddleWareBrowserLayer(BrowserLayer):

    def setup_middleware(self, app):
        return SillyMiddleWare(app)
