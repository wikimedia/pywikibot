***************
Pywikibot tests
***************

The Pywikibot tests are based on the `unittest framework
<https://docs.python.org/3/library/unittest.html>`_.

The tests package provides a function :func:`tests.load_tests` that supports
the `load tests protocol
<https://docs.python.org/3/library/unittest.html#load-tests-protocol>`_.
The default ordering begins with tests of underlying components, then tests
site and page semantics, and finishes with tests of the scripts and finally
any tests which have not been inserted into the ordered list of tests.

A function collector also exists in the 'tests' package.

Running tests
=============

Run all tests
-------------

The entire suite of tests may be run in the following ways from the root directory:

**Module unittest**

::

    python -m unittest discover -v -p "*_tests.py"

**pytest**

.. note:: Running the test suite with pytest requires Python 3.10 or higher.

::

    pip install "pytest >= 9.0.3"
    pytest

**tox**

::

    tox

Run specific tests
------------------

Individual test components can be run using unittest, pytest or pwb.
With -code and -family or -site options pwb can be used to specify a site.


**unittest**

::

    python -m unittest -v tests.api_tests tests.site_tests
    python -m unittest -v tests.api_tests.TestParamInfo.test_init

**pytest**

::

    py.test -s -v tests/api_tests.py tests/site_tests.py
    py.test -s -v tests/api_tests.py::TestParamInfo::test_init

**pwb**

::

    python pwb.py tests/api_tests -v
    python pwb.py tests/site_tests -v
    python pwb.py tests/api_tests -v TestParamInfo.test_init
    python pwb.py -site:wikipedia:de tests/page_tests -v TestPageObject

**env**

::

    PYWIKIBOT_TEST_MODULES=api,site python -m unittest -v


Environment variables
=====================

**PYWIKIBOT_TEST_LOGOUT**
  Used when a test is logging out the test user. This environment variable
  enables :source:`tests/site_login_logout_tests`. The environment setting is
  needed to ensure that these tests run in their own test action and does not
  interfere with other tests. Otherwise they could fail if the test user is
  logged out by the test. Only one instance must run this test script. Set this
  environment variable to run this test locally::

    PYWIKIBOT_TEST_LOGOUT=1

**PYWIKIBOT_TEST_MODULES**
  Only run tests given with this environment variable. Multiple tests must be
  separated by a ``,`` without any white space. For example to enable only
  :source:`tests/site_tests` and :source:`tests/wikibase_tests` set the
  environment variable as::

    PYWIKIBOT_TEST_MODULES=site,wikibase

  .. note:: test names must be given without subsequent ``_tests``.

**PYWIKIBOT_TEST_NO_RC**
  This environment variable disables recent changes tests and can be used to
  speed up tests. GitHub actions enables this setting for that purpose::

    PYWIKIBOT_TEST_NO_RC=1

**PYWIKIBOT_TEST_OAUTH**
  This environment variable holds the OAuth token. It is set by
  ``oauth_tests-ci.yml`` CI config file and is solely used by
  :source:`tests/oauth_tests`. You can use it for your private tests. The
  environment variable must contain consumer key and secret and access
  key and secret delimited by ``:`` as::

    PYWIKIBOT_TEST_OAUTH=consumer_key:consumer_secret:access_key:access_secret

**PYWIKIBOT_TEST_QUIET**
  This environment variable can be set for quiet mode. It prevents output by
  test package, i.e. 'max_retries reduced from x to y'. It is used by the
  :func:`tests.utils.execute` test runner. To enable it for other tests use::

        PYWIKIBOT_TEST_QUIET=1

**PYWIKIBOT_TEST_RUNNING**
  This environment variable ignores some passwordfile checks in
  :meth:`login.LoginManager.readPassword` and skips some tests instead of raising
  :exc:`exceptions.MaxlagTimeoutError` when maximum retries attempted due to
  maxlag without success. GitHub actions and Jenkins tests activate this variable::

    PYWIKIBOT_TEST_RUNNING=1

**PYWIKIBOT_TEST_WRITE**
  There are also several other 'write' tests which also attempt to perform
  write operations successfully.  These **will** write to the wikis, and they
  should always only write to 'test' wikis.

  .. version-changed:: 9.2
     Enabling them will also enable 'edit failure' tests which attempt to write
     to the wikis and **should** fail. If there is a bug in pywikibot or
     MediaWiki, these tests **may** actually perform a write operation.

  To enable 'write' tests, set::

    PYWIKIBOT_TEST_WRITE=1

.. version-removed:: 9.2
   The :envvar:`PYWIKIBOT_TEST_WRITE_FAIL` environment variable; use
   :envvar:`PYWIKIBOT_TEST_WRITE` instead.
.. version-removed:: 9.5
   The :envvar:`PYWIKIBOT_TEST_GUI` environment variable.

Instead of setting the environment by the os (or `os.environ` as well) you can use the :mod:`pwb`
wrapper script to set it::

    pwb PYWIKIBOT_TEST_WRITE=1 script_tests -v TestScriptSimulate.test_archivebot

The assignment can be omitted and defaults to 1. The following is equal to the line above::

    pwb PYWIKIBOT_TEST_WRITE script_tests -v TestScriptSimulate.test_archivebot

Decorators
==========

pywikibot's test suite, including Python's unittest module, provides decorators
to modify the behaviour of the test cases.

@unittest.skipIf
----------------
Skip a test if the condition is true. Refer to unittest's documentation.

::

  import unittest
  [......]
  @unittest.skipIf(check_if_fatal(), 'Something is not okay.')
  def test_skipIf(self):

@unittest.skipUnless
--------------------
Skip a test unless the condition is true. Refer to unittest's documentation.

::

  import unittest
  [......]
  @unittest.skipUnless(check_if_true(), 'Something must happen.')
  def test_skipUnless(self):

@tests.aspects.require_modules
-------------------------------
Require that the given list of modules can be imported.

::

  from tests.aspects import require_modules
  [......]
  @require_modules('important1', 'musthave2')
  def test_require_modules(self):

@tests.aspects.require_version
------------------------------
Require a given MediaWiki version

::

  from tests.aspects import require_version
  [......]
  @require_version('>=1.31.0')
  def test_require_version(self):

@unittest.mock.patch
-----------------------
Replaces `target` with object specified in `new`. Refer to mock's documentation.
This is especially useful in tests, where requests to third-parties should be
avoided.

::

  from unittest.mock import patch


  def fake_ping(url):
    return 'pong'
  [......]
  @patch('http_ping', side_effect=fake_ping)
  def test_patch(self):
    self.assertEqual('pong', http_ping())


Contributing tests
==================

The test package distinguishes between framework tests, which cover Pywikibot
framework components, and script tests, which cover individual Pywikibot
scripts.

Test modules should be named according to the Pywikibot component being
tested. For example, the module :mod:`pywikibot.page` is tested by
:source:`tests/page_tests`.

New test classes should be added to the existing test modules unless they
test a new component of Pywikibot.

All test classes must be a subclass of :class:`TestCase
<tests.aspects.TestCase>`. Its metaclass validates the declared test environment
and dynamically creates the required site objects. Tests can declare a specific
site, multiple sites, or other behaviour attributes as described in
:ref:`Test behaviour attributes`.


Test sites
----------

If a test depends on a specific site, add the class attributes ``family``
and ``code``:

::

    family = 'wikipedia'
    code = 'en'

Once declared, the Site object is available as ``self.site``.


If a test requires multiple specific sites, define the ``sites`` class
attribute. Each key becomes a separate test variant.

::

    sites = {
        'enwiki': {
            'family': 'wikipedia',
            'code': 'en',
        },
        'itwikt': {
            'family': 'wiktionary',
            'code': 'it',
        }
    }

To obtain the Site object, call :meth:`get_site<tests.TestCase.get_site>`
with the key given to the site:

::

    self.get_site('itwikt')

If a test method accepts the site key as its second positional argument,
the metaclass creates one test for each entry in ``sites`` and passes the
corresponding key to the test method:

::

    def test_something(self, site_key):
        site = self.get_site(site_key)

For tests which require network access to a host which is not a MediaWiki
API site, the class attribute 'sites' may include a hostname:

::

    sites = {
        'wdq': {
            'hostname': 'query.wikidata.org',
        }
    }

If no API site is used and only hosts are require, you may define
``hostname`` or ``hostnames``:

::

    hostname = 'query.wikidata.org'

or:

::

    hostnames = [
        'query.wikidata.org',
        'example.org',
    ]

The hosts are added to the test site's definitions and checked for network
availability.


Test behaviour attributes
-------------------------

The following class attributes control the behaviour of a test class.
Attributes which enable additional functionality are normally set to
``True``. Attributes which are not set keep their default behaviour.

Some attributes implicitly enable additional behaviour or add mixins to
the test class.


Caching
~~~~~~~

``cached = True``
    The test class may aggressively cache API responses. This adds
    :class:`ForceCacheMixin<tests.aspects.ForceCacheMixin>`. ``cached``
    is intended for read-only tests and must not be combined with
    ``write = True``.


Network access
~~~~~~~~~~~~~~

``net = True``
    The test class explicitly requires network access.

``net = False``
    The test class explicitly declares that no network access is used.

    Test classes which do not use a site must explicitly define ``net``.

``site = False``
    The test class does not use a Site object. This adds
    :class:`DisableSiteMixin<tests.aspects.DisableSiteMixin>` and prevents
    calls to :func:`pywikibot.Site`. ``site = False`` is commonly combined
    with ``net = False`` for tests which do not access a site or the network.

Disconnected site tests
~~~~~~~~~~~~~~~~~~~~~~~

``dry = True``
    The test class uses disconnected Site objects instead of accessing real
    sites. This adds :class:`DisconnectedSiteMixin
    <tests.aspects.DisconnectedSiteMixin>`. ``dry`` implicitly disables
    network access (equivalent to ``net = False``).


Authentication
~~~~~~~~~~~~~~

``login = True``
    The test class requires authentication on the configured site. This
    adds :class:`RequireLoginMixin<tests.aspects.RequireLoginMixin>`.

``oauth = True``
    The test class uses OAuth authentication when authentication is required.

``rights = '<rights>'``
    The test class requires specific user rights. Multiple rights must be
    separated by commas. Setting ``rights`` implicitly enables ``login = True``
    and adds :class:`NeedRightsMixin<tests.aspects.NeedRightsMixin>`.


Writing tests
~~~~~~~~~~~~~

``write = True``
    The test class performs write operations on a site. This adds
    :class:`SiteWriteMixin<tests.aspects.SiteWriteMixin>`. Setting ``write``
    implicitly enables ``login = True``. Write tests require explicit enabling
    through the test environment ``PYWIKIBOT_TEST_WRITE``.


Script execution
~~~~~~~~~~~~~~~~

``pwb = True``
    The test class invokes scripts through :mod:`pwb`. Test classes using
    ``pwb`` normally require a configured site. If a ``pwb`` test does not
    use a site, it must explicitly define ``site = False``.


Wikibase tests
~~~~~~~~~~~~~~

``wikibase = True``
    The test class requires sites with a Wikibase data repository. This
    is used by :class:`WikibaseTestCase<tests.aspects.WikibaseTestCase>`.
