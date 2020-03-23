=======
CHANGES
=======

4.2.0 (2020-03-23)
------------------

- Add support for Python 3.7 and 3.8.

- Drop support for Python 3.3 and 3.4.

- Fix the testlayer's ``http()`` to accept leading whitespace in HTTP requests,
  for compatibility with zope.app.testing.functional's HTTPCaller.

- Add a ``server_protocol`` attribute to ``FakeResponse`` so you can customize
  the output to be more compatible with zope.app.testing.functional's
  HTTPCaller.

- Drop support for running the tests using ``python setup.py test``.


4.1.0 (2017-04-27)
------------------

- Use ``base64.b64encode`` to avoid deprecation warning with Python 3.

- Add support for PyPy.

- Add support for Python 3.6.

- Fix the testlayer's ``FakeResponse`` assuming that headers were in
  unicode on Python 2, where they should usually be encoded bytes
  already. This could lead to UnicodeDecodeError if the headers
  contained non-ascii characters. Also make it implement
  ``__unicode__`` on Python 2 and ``__bytes__`` on Python 3 to ease
  cross version testing. See `issue 7 <https://github.com/zopefoundation/zope.app.wsgi/issues/7>`_.

4.0.0 (2016-08-08)
------------------

- Update dependencies to no longer pin alpha versions of packages which already
  have final releases.

- Drop support for Python 2.6.

- Claim support for Python 3.4 and 3.5. This requires to update to

  - ``zope.app.appsetup`` >= 4.0

  - ``zope.app.publication`` >= 4.0

- Fix a bug occurring in Python 3 when the principal could not be adapted to
  `ILoggingInfo`.

4.0.0a4 (2013-03-19)
--------------------

- Improve Trove classifiers.

- Fix ``BrowserLayer(allowTearDown=True)`` to actually allow tear downs.


4.0.0a3 (2013-03-03)
--------------------

- You can now specify additional WSGI middleware components wihtout
  subclassing the ``BrowserLayer`` class.

- `tox` now uses the Zope test runner's `ftest` command to execute tests,
  since setup tests cannot deal with layers, especially when they need to
  spawn sub-proceeses.

- Switched all functional tests to use `WebTest` instead of
  ``zope.testbrowser``. Set up proper layering.

- Do not rely on ``zope.testbrowser.wsgi`` WSGI layer support. It was not
  needed anyways.

- Minimized the ``ftesting.zcml`` setup.

- Backwards incompatibility: if you depend on ``zope.app.wsgi.testlayer``, you
  will need to require ``zope.app.wsgi[testlayer] >= 4.0`` (version constraint
  is there because older zope.app.wsgi releases did not define a ``testlayer``
  extra).


4.0.0a2 (2013-03-02)
--------------------

- Fixed a bug in WSGI Test Layer setup, where the DB is not correctly set.


4.0.0a1 (2013-02-28)
--------------------

- Added support for Python 3.3.

- Replaced deprecated ``zope.interface.implements`` usage with equivalent
  ``zope.interface.implementer`` decorator.

- Dropped support for Python 2.4 and 2.5.


3.15.0 (2012-01-19)
-------------------

- Fixed: zope.app.wsgi.paste.ZopeApplication didn't emit
  ProcessStarting events.

  **NOTE**
    If an application compensated for this by generating the event, it
    will need to stop or there will be multiple events
    emited. (Whether or not multiple events will do any harm is
    application specific.)

3.14.0 (2012-01-10)
-------------------

- Set the WSGI environment's ``REMOTE_USER`` item (if not already set)
  with the Zope principal label. (This is the same data set in
  the ``wsgi.logging_info`` environment item.)

  This change allows user info to be used by `paste.translogger
  <http://pythonpaste.org/modules/translogger.html>`_ middleware (or
  any similar middleware that uses ``REMOTE_USER``), which provides
  access logging.


3.13.0 (2011-03-15)
-------------------

- Update to zope.testbrowser 4.0.0 which uses WebTest instead of wsgi_intercept.


3.12.0 (2011-01-25)
-------------------

- Fixed ``zope.app.wsgi.testlayer.http`` to work with changes made in
  version 3.11.0.


3.11.0 (2011-01-24)
-------------------

- Moved `wsgi_intercept` support to ``zope.testbrowser.wsgi``, thus
  requiring at least version 3.11 of this package:

  - Moved ``zope.app.wsgi.testlayer.Browser`` to
    ``zope.testbrowser.wsgi.Browser``, but left BBB import here.

  - Split up ``zope.app.wsgi.testlayer.BrowserLayer`` into generic WSGI
    browser layer (``zope.testbrowser.wsgi.Layer``) and ZODB/ZOPE specific
    part (``zope.app.wsgi.testlayer.BrowserLayer`` as before).


3.10.0 (2010-11-18)
-------------------

- Add pluggability for setting up WSGI middleware in testlayer.


3.9.3 (2010-10-14)
------------------

- Python 2.7 compatibility for xmlrpc. Transplant of zope.app.testing r116141.


3.9.2 (2010-05-23)
------------------

- Fixed test breakage due to changes in mechanize 0.2.0.


3.9.1 (2010-04-24)
------------------

- Add support for testing XMLRPC using zope.app.wsgi.testlayer.

- Fix a bug in the status string handling in zope.app.wsgi.testlayer's
  FakeResponse.


3.9.0 (2010-04-19)
------------------

- Return a FakeResponse object in zope.app.wsgi.testlayer.http,
  so it becomes easier to port over tests from zope.app.testing's
  HTTPCaller.

- X-Powered-By header is now stripped by zope.app.wsgi.testlayer as
  it is by zope.app.testing.

- Bugfix: initialize any <logger> defined in the config, as
  zope.app.server does. (Fixes #291147)


3.8.0 (2010-04-14)
------------------

- zope.app.wsgi.testlayer is now a lot more compatible with
  the HTTPCaller() functionality in zope.app.testing, which it can
  replace:

  - same transaction behavior - pending transactions are committed
    before request and synchronized afterwards.

  - support for browser.handleErrors (for zope.testbrowser).

  - support for clear-text (non-base64) Basic authentication headers,
    which are easier to read in the tests (though not correct in
    actual HTTP traffic).


3.7.0 (2010-04-13)
------------------

- Rewrite tests in order not to dependent on ``zope.app.testing`` and
  ``zope.app.zcmlfiles``.

- ``zope.app.wsgi.testlayer`` introduces new testing functionality that
  can replace the old functionality in ``zope.app.testing``. In addition,
  it supports using ``zope.testbrowser`` with WSGI directly (instead of
  relying on ``zope.app.testing``, which pulls in a lot of dependencies).

  The interesting parts are:

  * ``zope.app.wsgi.testlayer.BrowserLayer``: this sets up a minimal layer
    that allows you to use the new WSGI-enabled Browser.

  * ``zope.app.wsgi.testlayer.Browser``: this is a subclass of Browser from
    ``zope.testbrowser.browser``. Use it instead of
    ``zope.testbrowser.browser`` directly to use the test browser with WSGI.
    You need to use ``BrowserLayer`` with your tests for this to work.

  * ``zope.app.wsgi.testlayer.http``: this is the equivalent to the ``http()``
    function in ``zope.app.testing``. It allows low-level HTTP access
    through WSGI. You need to use ``BrowserLayer`` with your tests for
    this to work.


3.6.1 (2010-01-29)
------------------

- Support product configuration sections in Zope configuration files.


3.6.0 (2009-06-20)
------------------

- Import database events directly from ``zope.processlifetime``
  instead of using BBB imports in ``zope.app.appsetup``.


3.5.2 (2009-04-03)
------------------

- The ``WSGIPublisherApplication`` uses now the ``ILoggingInfo`` concept given
  from zope.publisher.interfaces.logginginfo for log user infos usable for
  access logs. This allows you to implement your own access log user info
  message. See zope.publisher.interfaces.logginginfo.ILoggingInfo for more
  information.


3.5.1 (2009-03-31)
------------------

- The ``WSGIPublisherApplication`` call now provides a user name
  in the environment meant for use in logs.


3.5.0 (2009-02-10)
------------------

- Make devmode warning message more generic. We don't nesessary have the
  `etc/zope.conf` file nowadays when using buildout-based setups.

- Add an application factory for Paste. So Zope application can now be
  easily deployed with Paste .ini configuration like this::

    [app:main]
    use = egg:zope.app.wsgi
    config_file = %(here)s/zope.conf
    handle_errors = false

  The config_file is a required argument, however the handle_errors
  defaults to True if not specified. Setting it to False allows you to
  make WSGIPublisherApplication not handle exceptions itself but
  propagate them to an upper middleware, like WebError or something.

- The ``WSGIPublisherApplication`` constructor and ``getWSGIApplication``
  function now accept optional ``handle_errors`` argument, described
  above.

- Change mailing list address to zope-dev at zope.org instead of retired
  one.


3.4.1 (2008-07-30)
------------------

- Added Trove classifiers.

- Notify ``WSGIPublisherApplicationCreated`` event when WSGI application is
  created.

- Fixed deprecation warning in ``ftesting.zcml``: ZopeSecurityPolicy moved to
  ``zope.securitypolicy``.


3.4.0 (2007-09-14)
------------------

- Fixed the tests to run on Python 2.5 as well as Python 2.4.

- Split ``getApplication`` into ``config`` and ``getApplication`` so
  that ``config`` could be reused, for example for debugging.


3.4.0a1 (2007-04-22)
--------------------

Initial release as a separate project, corresponds to ``zope.app.wsgi``
from Zope 3.4.0a1
