##############################################################################
#
# Copyright (c) 2009 Zope Foundation and Contributors.
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
"""An application factory for Paste

$Id$
"""
from zope.app.wsgi import getWSGIApplication
import zope.event
import zope.processlifetime

from zope.app.wsgi._compat import PYTHON3

if PYTHON3:
    basestring = (str, bytes)

def asbool(obj):
    if isinstance(obj, basestring):
        obj = obj.lower()
        if obj in ('1', 'true', 'yes', 't', 'y'):
            return True
        if obj in ('0', 'false', 'no', 'f', 'n'):
            return False
    return bool(obj)


def ZopeApplication(global_config, config_file, handle_errors=True, **options):
    handle_errors = asbool(handle_errors)
    app = getWSGIApplication(config_file, handle_errors=handle_errors)
    zope.event.notify(zope.processlifetime.ProcessStarting())
    return app
