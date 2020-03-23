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
"""
import os
from setuptools import setup, find_packages

TESTS_REQUIRE = [
    'WebTest',
    'zope.annotation',
    'zope.authentication',
    'zope.browserpage',
    'zope.login',
    'zope.password',
    'zope.principalregistry >=4.0.0a1',
    'zope.securitypolicy >=4.0.0a1',
    'zope.testing',
    'zope.testrunner',
]


def read(*rnames):
    with open(os.path.join(os.path.dirname(__file__), *rnames)) as f:
        return f.read()


setup(
    name='zope.app.wsgi',
    version='4.2.0',
    url='https://github.com/zopefoundation/zope.app.wsgi',
    license='ZPL 2.1',
    description='WSGI application for the zope.publisher',
    long_description=read('README.rst') +
        '\n\n' +
        read('CHANGES.rst'),
    author='Zope Foundation and Contributors',
    author_email='zope-dev@zope.org',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Zope Public License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
        'Framework :: Zope :: 3',
    ],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['zope', 'zope.app'],
    extras_require=dict(
        test=TESTS_REQUIRE,
        testlayer=['WebTest'],
    ),
    install_requires=[
        'setuptools',
        'ZConfig',
        'transaction',
        'zope.app.appsetup >= 4.0',
        'zope.processlifetime',
        'zope.app.publication >= 4.0',
        'zope.event',
        'zope.interface',
        'zope.publisher>=4.0.0a3',
        'zope.security>4.0.0a2',
        'zope.component',
        'zope.configuration',
        'zope.container >=4.0.0a1',
        'zope.error',
        'zope.lifecycleevent',
        'zope.session >= 4.0.0a1',
        'zope.site >= 4.0.0a1',
        'zope.testing',
        'zope.traversing>=4.0.0a1',
    ],
    tests_require=TESTS_REQUIRE,
    entry_points={
        'paste.app_factory': [
            'main = zope.app.wsgi.paste:ZopeApplication'
        ]
    },
    include_package_data=True,
    zip_safe=False,
)
