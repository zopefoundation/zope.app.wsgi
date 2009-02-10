##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors.
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
"""Setup for zope.app.wsgi package

$Id$
"""
from setuptools import setup, find_packages, Extension

setup(name='zope.app.wsgi',
      version = '3.5.0dev',
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
      extras_require = dict(test=['zope.app.testing',
                                  'zope.app.securitypolicy',
                                  'zope.app.zcmlfiles',
                                  'zope.testbrowser']),
      install_requires=['setuptools',
                        'ZConfig',
                        'zope.app.appsetup',
                        'zope.app.publication',
                        'zope.event',
                        'zope.interface',
                        'zope.publisher',
                        'zope.security',
                        ],
      entry_points={
          'paste.app_factory': [
              'main = zope.app.wsgi.paste:ZopeApplication'
          ]
      },
      include_package_data = True,
      zip_safe = False,
      )
