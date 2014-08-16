===============
Pywikibot tests
===============

The Pywikibot tests are based on the unittest framework
<https://docs.python.org/2/library/unittest.html>,
and are compatible with nose.<https://nose.readthedocs.org/>

The tests package provides a function load_tests that supports the
'load tests protocol'.
<https://docs.python.org/2/library/unittest.html#load-tests-protocol>.
The default ordering begins with tests of underlying components, then tests
site and page semantics, and finishes with tests of the scripts and tests
which are not yet included in the ordered tests.

A function collector also exists in the 'tests' package.

Running tests
=============

All tests
---------

The entire suite of tests may be run in three ways from the root directory:

setup.py
~~~~~~~~

::

    python setup.py test

Module unittest
~~~~~~~~~~~~~~~

::

    python -m unittest -v

nose
~~~~

::

    nosetests -v

Specific tests
--------------

Individual test components can be run using unittest, nosetests, or pwb

unittest
~~~~~~~~

::

    python -m unittest -v tests.site_tests

nose
~~~~

::

    nosetests -v tests.site_tests

pwb
~~~

::

    python pwb.py tests/site_tests.py -v


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

Other class attributes
----------------------

- 'net = False' : test class does not use a site
- 'user = True' : test class needs to login to site
- 'write = True' : test class needs to write to a site

