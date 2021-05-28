##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
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
"""Python-3 Compatibility module
"""

import sys
PYTHON2 = sys.version_info[0] == 2
PYTHON3 = sys.version_info[0] == 3

if PYTHON2:  # pragma: PY2
    _u = unicode  # noqa: F821 undefined name
    import xmlrpclib as xmlrpcclient
    import httplib as httpclient
    import types
    FileType = types.FileType
else:  # pragma: PY3
    _u = str
    import xmlrpc.client as xmlrpcclient  # noqa: F401 imported but unused
    import http.client as httpclient  # noqa: F401 imported but unused
    import io
    FileType = io._io._IOBase
