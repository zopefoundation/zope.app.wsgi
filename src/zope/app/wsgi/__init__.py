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
"""A WSGI Application wrapper for zope

$Id$
"""
import os
import sys
import logging
import ZConfig
import zope.processlifetime
import zope.app.appsetup.product

from zope.event import notify
from zope.interface import implements
from zope.publisher.publish import publish
from zope.publisher.interfaces.logginginfo import ILoggingInfo

from zope.app.appsetup import appsetup
from zope.app.publication.httpfactory import HTTPPublicationRequestFactory
from zope.app.wsgi import interfaces


class WSGIPublisherApplication(object):
    """A WSGI application implementation for the zope publisher

    Instances of this class can be used as a WSGI application object.

    The class relies on a properly initialized request factory.
    """
    implements(interfaces.IWSGIApplication)

    def __init__(self, db=None, factory=HTTPPublicationRequestFactory,
                 handle_errors=True):
        self.requestFactory = None
        self.handleErrors = handle_errors

        if db is not None:
            self.requestFactory = factory(db)

    def __call__(self, environ, start_response):
        """See zope.app.wsgi.interfaces.IWSGIApplication"""
        request = self.requestFactory(environ['wsgi.input'], environ)

        # Let's support post-mortem debugging
        handle_errors = environ.get('wsgi.handleErrors', self.handleErrors)

        request = publish(request, handle_errors=handle_errors)
        response = request.response
        # Get logging info from principal for log use
        logging_info = ILoggingInfo(request.principal, None)
        if logging_info is None:
            message = '-'
        else:
            message = logging_info.getLogMessage()
        environ['wsgi.logging_info'] = message

        # Start the WSGI server response
        start_response(response.getStatusString(), response.getHeaders())

        # Return the result body iterable.
        return response.consumeBodyIter()


class PMDBWSGIPublisherApplication(WSGIPublisherApplication):

    def __init__(self, db=None, factory=HTTPPublicationRequestFactory,
                 handle_errors=False):
        super(PMDBWSGIPublisherApplication, self).__init__(db, factory,
                                                           handle_errors)

    def __call__(self, environ, start_response):
        environ['wsgi.handleErrors'] = self.handleErrors

        # Call the application to handle the request and write a response
        try:
            app = super(PMDBWSGIPublisherApplication, self)
            return app.__call__(environ, start_response)
        except Exception, error:
            import sys
            import pdb
            print "%s:" % sys.exc_info()[0]
            print sys.exc_info()[1]
            try:
                pdb.post_mortem(sys.exc_info()[2])
                raise
            finally:
                pass


def config(configfile, schemafile=None, features=()):
    # Load the configuration schema
    if schemafile is None:
        schemafile = os.path.join(
            os.path.dirname(appsetup.__file__), 'schema', 'schema.xml')

    # Let's support both, an opened file and path
    if isinstance(schemafile, basestring):
        schema = ZConfig.loadSchema(schemafile)
    else:
        schema = ZConfig.loadSchemaFile(schemafile)

    # Load the configuration file
    # Let's support both, an opened file and path
    try:
        if isinstance(configfile, basestring):
            options, handlers = ZConfig.loadConfig(schema, configfile)
        else:
            options, handlers = ZConfig.loadConfigFile(schema, configfile)
    except ZConfig.ConfigurationError, msg:
        sys.stderr.write("Error: %s\n" % str(msg))
        sys.exit(2)

    # Insert all specified Python paths
    if options.path:
        sys.path[:0] = [os.path.abspath(p) for p in options.path]

    # Parse product configs
    zope.app.appsetup.product.setProductConfigurations(
        options.product_config)

    # Setup the event log
    options.eventlog()

    # Setup other defined loggers
    for logger in options.loggers:
        logger()

    # Insert the devmode feature, if turned on
    if options.devmode:
        features += ('devmode',)
        logging.warning("Developer mode is enabled: this is a security risk "
            "and should NOT be enabled on production servers. Developer mode "
            "can usually be turned off by setting the `devmode` option to "
            "`off` or by removing it from the instance configuration file "
            "completely.")

    # Execute the ZCML configuration.
    appsetup.config(options.site_definition, features=features)

    # Connect to and open the database, notify subscribers.
    db = appsetup.multi_database(options.databases)[0][0]
    notify(zope.processlifetime.DatabaseOpened(db))

    return db


def getWSGIApplication(configfile, schemafile=None, features=(),
                       requestFactory=HTTPPublicationRequestFactory,
                       handle_errors=True):
    db = config(configfile, schemafile, features)
    application = WSGIPublisherApplication(db, requestFactory, handle_errors)

    # Create the application, notify subscribers.
    notify(interfaces.WSGIPublisherApplicationCreated(application))

    return application
