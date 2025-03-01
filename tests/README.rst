***************
Pywikibot tests
***************

The Pywikibot tests are based on the `unittest framework
<https://docs.python.org/3/library/unittest.html>`_.

The tests package provides a function load_tests that supports the
`load tests protocol
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

::

    pip install pytest
    pytest

**tox**

::

    tox

Run specific tests
------------------

Individual test components can be run using unittest, pytest or pwb.
With -lang and -family or -site options pwb can be used to specify a site.


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
    python pwb.py -lang:de -family:wikipedia tests/page_tests -v TestPageObject

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
  This environment variable holds the Oauth token. It is set by
  ``oauth_tests-ci.yml`` CI config file and is solely used by
  :source:`tests/oauth_tests`. You can use it for your private tests. The
  environment variable must contain consumer key and secret and access
  key and secret delimited by ``:`` as::

    PYWIKIBOT_TEST_OAUTH=consumer_key:consumer_secret:access_key:access:secret

**PYWIKIBOT_TEST_QUIET**
  This environment variable can be set for quit mode. It prevents output by
  test package, i.e. 'max_retries reduced from x to y'. It is used be the
  :func:`tests.utils.execute` test runner. To enable it for other tests use::

        PYWIKIBOT_TEST_QUIET=1

**PYWIKIBOT_TEST_RUNNING**
  This environment variable skips tests instead of raising
  :exc:`exceptions.MaxlagTimeoutError` when maximum retries attempted due to
  maxlag without success. It is also used by :source:`tests/script_tests` for code
  coverage. GitHub actions and AppVeyor tests activate this variable::

    PYWIKIBOT_TEST_RUNNING=1

**PYWIKIBOT_TEST_WRITE**
  There are also several other 'write' tests which also attempt to perform
  write operations successfully.  These **will** write to the wikis, and they
  should always only write to 'test' wikis.

  .. versionchanged:: 9.2
     Enabling them will also enable 'edit failure' tests which attempt to write
     to the wikis and **should** fail. If there is a bug in pywikibot or
     MediaWiki, these tests **may** actually perform a write operation.

  To enable 'write' tests, set::

    PYWIKIBOT_TEST_WRITE=1

.. versionremoved:: 9.2
   The :envvar:`PYWIKIBOT_TEST_WRITE_FAIL` environment variable; use
   :envvar:`PYWIKIBOT_TEST_WRITE` instead.
.. versionremoved:: 9.5
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

Test modules should be named according to the pywikibot that is being tested.
e.g. the module pywikibot.page is tested by tests.page_tests.

New test classes should be added to the existing test modules unless it
tests a new component of pywikibot.

All test classes must be a subclass of tests.aspects.TestCase, which uses a
metaclass to dynamically check the test can be run on a specified site, or
run a test on multiple sites.

Test sites
----------

If a test depends on a specific site, add class attributes 'family' and code'.

::

    family = 'wikipedia'
    code = 'en'

Once declared, the Site object can be accessed at self.site.


If a test requires multiple specific sites, add a class attribute 'sites'.

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

To obtain the Site object, call self.get_site with the key given to the site.

::

    self.get_site('itwikt')

For tests which require network access to a website which is not an APISite,
the class attribute 'sites' may include a hostname.

::

    sites = {
        'wdq':
            'hostname': 'wdq.wmflabs.org',
        }
    }


Other class attributes
----------------------

- ``net = False``: test class does not use a site
- ``dry = True``: test class can use a fake site object
- ``cached = True``: test class may aggressively cache API responses
- ``login = True``: test class needs to login to site
- ``rights = '<rights>'``: test class needs specific rights. Multiple rights  must be delimited with ``,``.
- ``write = True``: test class needs to write to a site
