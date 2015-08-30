===============
Pywikibot tests
===============

The Pywikibot tests are based on the `unittest framework
<https://docs.python.org/2/library/unittest.html>`_,
and are compatible with `nose <https://nose.readthedocs.org/>`_.

The tests package provides a function load_tests that supports the
`load tests protocol
<https://docs.python.org/2/library/unittest.html#load-tests-protocol>`_.
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

    python setup.py test

::

    python setup.py nosetests --tests tests


Module unittest
~~~~~~~~~~~~~~~

::

    python -m unittest -v

nose
~~~~

::

    nosetests -v

tox
~~~

::

    tox

Specific tests
--------------

Individual test components can be run using unittest, nosetests, or pwb

unittest
~~~~~~~~

::

    python -m unittest -v tests.api_tests tests.site_tests

nose
~~~~

::

    nosetests -v tests.api_tests tests.site_tests

pwb
~~~

::

    python pwb.py tests/api_tests.py -v
    python pwb.py tests/site_tests.py -v

env
~~~

::

    PYWIKIBOT_TEST_MODULES=api,site python setup.py test


Travis CI
=========

After changes are published into a github repository, tests may be run on
travis-ci.org according to the configuration in .travis.yml .

When changes are merged into the main repository, they are replicated to
https://github.com/wikimedia/pywikibot-core , and travis tests are run and
published at travis-ci.org/wikimedia/pywikibot-core/builds .  These tests
use the Wikimedia global (SUL) account 'Pywikibot-test', which has a password
securely stored in .travis.yml . See section env:global:secure.

Anyone can run these tests on travis-ci.org using their own github account, with
code changes that have not been merged into the main repository.  To do this:

1. create a github and travis-ci account
2. fork the main github repository https://github.com/wikimedia/pywikibot-core
3. enable builds from the travis profile page: https://travis-ci.org/profile
4. push changes into the forked git repository
5. watch the build at https://travis-ci.org/<username>/pywikibot-core/builds

Only travis-ci builds from the main repository can access the password for the
Wikimedia account 'Pywikibot-test'.  All tests which require a logged in user
are skipped if the travis-ci build environment does not have a password.

To enable 'user' tests on travis-ci builds for a different repository, add
a username and password to travis:

1. Go to https://travis-ci.org/<username>/pywikibot-core/settings/env_vars
2. Add a new variable named PYWIKIBOT2_USERNAME and a value of a valid
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
travis tests, using a password that is not shared with trusted accounts.

Appveyor CI
===========

After changes are published into a github repository, tests may be run on
a Microsoft Windows box provided by ci.appveyor.com according to the
configuration in .appveyor.yml .  To do this:

1. create a github and appveyor account
2. fork the main github repository
3. create a project in ci.appveyor.com
4. go to https://ci.appveyor.com/project/<username>/pywikibot-core/settings
   and enter the custom configuration .yml filename: .appveyor.yml
5. push changes into the forked git repository
6. watch the build at https://ci.appveyor.com/<username>/pywikibot-core/history

The 'user' tests are not yet enabled on appveyor builds.

CircleCI
========

After changes are published into a github repository, tests may be run on
CircleCI Ubuntu servers.

1. create a github and circleci account
2. fork the main github repository
3. create a project in circleci.com
4. go to https://circleci.com/gh/<username>/pywikibot-core/edit#env-vars
   and add the following variables:
     PYWIKIBOT2_NO_USER_CONFIG=2
     TOXENV=py27,py34
5. push changes into the forked git repository
6. watch the build at https://circleci.com/gh/<username>/pywikibot-core

PYWIKIBOT2_NO_USER_CONFIG=2 is needed because 'python setup.py test' is run.

TOXENV=py27,py34 is a workaround because CircleCI runs 'tox',
but there is a bug in the CircleCI default 'py26' implementation.

This approach does not include 'user' tests.

Environment variables
=====================

There are a set of 'edit failure' tests, which attempt to write to the wikis
and **should** fail.  If there is a bug in pywikibot or MediaWiki, these
tests **may** actually perform a write operation.

These 'edit failure' tests are disabled by default. On Travis they are enabled
by default on builds by any other github account except 'wikimedia'.

To disable 'edit failure' tests, set PYWIKIBOT2_TEST_WRITE_FAIL=0

There are also several other 'write' tests which also attempt to perform
write operations successfully.  These **will** write to the wikis, and they
should always only write to 'test' wikis.

These 'write' tests are disabled by default, and currently can not be
run on travis or appveyor as they require interaction using a terminal. Also
enabling them won't enable 'edit failure' tests.

To enable 'write' tests, set PYWIKIBOT2_TEST_WRITE=1

Enabling only 'edit failure' tests or 'write' tests won't enable the other tests
automatically.

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
- ``user = True`` : test class needs to login to site
- ``sysop = True`` : test class needs to login to site as a sysop
- ``write = True`` : test class needs to write to a site

