##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
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
# This package is developed by the Zope Toolkit project, documented here:
# http://docs.zope.org/zopetoolkit
# When developing and releasing this package, please follow the documented
# Zope Toolkit policies as described by this documentation.
##############################################################################
"""Setup for zope.app.wsgi package

$Id$
"""
from setuptools import setup, find_packages

setup(name='zope.app.wsgi',
      version='3.10.0',
      url='http://pypi.python.org/pypi/zope.app.wsgi',
      license='ZPL 2.1',
      description='WSGI application for the zope.publisher',
      long_description=\
          open('README.txt').read() + \
          '\n\n' + \
          open('CHANGES.txt').read(),
      author='Zope Corporation and Contributors',
      author_email='zope-dev@zope.org',
      classifiers=['Environment :: Web Environment',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: Zope Public License',
                   'Programming Language :: Python',
                   'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
                   'Framework :: Zope3',
                   ],

      packages=find_packages('src'),
      package_dir = {'': 'src'},
      namespace_packages=['zope', 'zope.app'],
      extras_require = dict(test=[
          'zope.annotation',
          'zope.authentication',
          'zope.browserpage',
          'zope.componentvocabulary',
          'zope.location',
          'zope.login',
          'zope.password',
          'zope.principalregistry',
          'zope.securitypolicy',
          ]),
      install_requires=[
          'setuptools',
          'ZConfig',
          'wsgi_intercept',
          'ZODB3',
          'zope.app.appsetup >= 3.14.0',
          'zope.processlifetime',
          'zope.app.publication',
          'zope.event',
          'zope.interface',
          'zope.publisher',
          'zope.security',
          'zope.component',
          'zope.configuration',
          'zope.container',
          'zope.error',
          'zope.lifecycleevent',
          'zope.session',
          'zope.site',
          'zope.testbrowser',
          'zope.testing',
          'zope.traversing',
          ],
      entry_points={
          'paste.app_factory': [
              'main = zope.app.wsgi.paste:ZopeApplication'
          ]
      },
      include_package_data = True,
      zip_safe = False,
      )
