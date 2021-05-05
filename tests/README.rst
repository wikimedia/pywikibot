===============
Pywikibot tests
===============

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

All tests
---------

The entire suite of tests may be run in the following ways from the root directory:

setup.py
~~~~~~~~

::

    pip install pytest-runner
    python setup.py pytest

Module unittest
~~~~~~~~~~~~~~~

::

    python -m unittest discover -v -p "*_tests.py"

pytest
~~~~~~

::

    py.test

tox
~~~

::

    tox

Specific tests
--------------

Individual test components can be run using unittest, pytest or pwb.
With -lang and -family or -site options pwb can be used to specify a site.


unittest
~~~~~~~~

::

    python -m unittest -v tests.api_tests tests.site_tests
    python -m unittest -v tests.api_tests.TestParamInfo.test_init

pytest
~~~~~~

::

    py.test -s -v tests/api_tests.py tests/site_tests.py
    py.test -s -v tests/api_tests.py::TestParamInfo::test_init

pwb
~~~

::

    python pwb.py tests/api_tests -v
    python pwb.py tests/site_tests -v
    python pwb.py tests/api_tests -v TestParamInfo.test_init
    python pwb.py -lang:de -family:wikipedia tests/page_tests -v TestPageObject

env
~~~

::

    PYWIKIBOT_TEST_MODULES=api,site python -m unittest -v


Travis CI
=========

After changes are published into a GitHub repository, tests may be run on
travis-ci.org according to the configuration in .travis.yml .

When changes are merged into the main repository, they are replicated to
https://github.com/wikimedia/pywikibot , and Travis tests are run and
published at https://travis-ci.org/wikimedia/pywikibot/builds .  These tests
use the Wikimedia global (SUL) account 'Pywikibot-test', which has a password
securely stored in .travis.yml file. See section env:global:secure.

Anyone can run these tests on travis-ci.org using their own GitHub account, with
code changes that have not been merged into the main repository. To do this:

1. create a GitHub and travis-ci account
2. fork the main GitHub repository https://github.com/wikimedia/pywikibot
3. enable builds from the Travis profile page: https://travis-ci.org/profile
4. push changes into the forked git repository
5. watch the build at https://travis-ci.org/<username>/pywikibot/builds

Only travis-ci builds from the main repository can access the password for the
Wikimedia account 'Pywikibot-test'. All tests which require a logged in user
are skipped if the travis-ci build environment does not have a password.

To enable 'user' tests on travis-ci builds for a different repository, add
a username and password to Travis:

1. Go to https://travis-ci.org/<username>/pywikibot/settings
2. Add a new variable named PYWIKIBOT_USERNAME and a value of a valid
   Wikimedia SUL username
3. Add another variable named USER_PASSWORD, with the private password for
   the Wikimedia SUL username used in step 2.  Check that this
   environment variable has "Display value in build logs" set to OFF, so
   the password does not leak into the build logs.
4. The next build should run tests that require a logged in user

If the username does not exist on one of the Travis build sites, user tests
will not be run on that build site.

While passwords in travis-ci environment variables are not leaked in normal
operations, you are responsible for your own passwords. If the variables contain
single quotes it is necessary to surround them in double quotes (see also
`travis-ci #4350 <https://github.com/travis-ci/travis-ci/issues/4350>`_).

It is strongly recommended that an untrusted bot account is created for
Travis tests, using a password that is not shared with trusted accounts.

AppVeyor CI
===========

After changes are published into a GitHub repository, tests may be run on
a Microsoft Windows box provided by ci.appveyor.com according to the
configuration in .appveyor.yml file. To do this:

1. create a GitHub and AppVeyor account
2. fork the main GitHub repository
3. create a project in ci.appveyor.com
4. go to https://ci.appveyor.com/project/<username>/pywikibot/settings
   and enter the custom configuration .yml filename: .appveyor.yml
5. push changes into the forked git repository
6. watch the build at https://ci.appveyor.com/<username>/pywikibot/history

The 'user' tests are not yet enabled on AppVeyor builds.

CircleCI
========

After changes are published into a GitHub repository, tests may be run on
CircleCI Ubuntu servers.

1. create a GitHub and CircleCI account
2. fork the main GitHub repository
3. create a project in circleci.com
4. go to https://circleci.com/gh/<username>/pywikibot/edit#env-vars
   and add the following variables:

     - PYWIKIBOT_NO_USER_CONFIG=2
     - TOXENV=py27,py34

5. push changes into the forked git repository
6. watch the build at https://circleci.com/gh/<username>/pywikibot

PYWIKIBOT_NO_USER_CONFIG=2 is needed because 'python -m unittest' is run.

TOXENV=py27,py34 is a workaround because CircleCI runs 'tox',
but there is a bug in the CircleCI default 'py26' implementation.

This approach does not include 'user' tests.

Environment variables
=====================

There are a set of 'edit failure' tests, which attempt to write to the wikis
and **should** fail. If there is a bug in pywikibot or MediaWiki, these
tests **may** actually perform a write operation.

These 'edit failure' tests are disabled by default. On Travis they are enabled
by default on builds by any other GitHub account except 'wikimedia'.

To disable 'edit failure' tests, set PYWIKIBOT_TEST_WRITE_FAIL=0

There are also several other 'write' tests which also attempt to perform
write operations successfully.  These **will** write to the wikis, and they
should always only write to 'test' wikis.

These 'write' tests are disabled by default, and currently cannot be
run on Travis or AppVeyor as they require interaction using a terminal. Also
enabling them won't enable 'edit failure' tests.

To enable 'write' tests, set PYWIKIBOT_TEST_WRITE=1

Enabling only 'edit failure' tests or 'write' tests won't enable the other tests
automatically.

Decorators
=====================

pywikibot's test suite, including Python's unittest module, provides decorators
to modify the behaviour of the test cases.

@unittest.skipIf
-----------------
Skip a test if the condition is true. Refer to unittest's documentation.

::

  import unittest
  [......]
  @unittest.skipIf(check_if_fatal(), 'Something is not okay.')
  def test_skipIf(self):

@unittest.skipUnless
---------------------
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
  @require_modules(['important1', 'musthave2'])
  def test_require_modules(self):

@unittest.mock.patch
-----------------------
Replaces `target` with object specified in `new`. Refer to mock's documentation.
This is especially useful in tests, where requests to third-parties should be
avoided.

::

  from tests import patch


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

- ``net = False`` : test class does not use a site
- ``dry = True`` : test class can use a fake site object
- ``cached = True``:  test class may aggressively cache API responses
- ``login = True`` : test class needs to login to site
- ``sysop = True`` : test class needs to login to site as a sysop
- ``write = True`` : test class needs to write to a site
