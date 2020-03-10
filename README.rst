.. image:: https://travis-ci.org/wikimedia/pywikibot.svg?branch=master
   :alt: Travis Build Status
   :target: https://travis-ci.org/wikimedia/pywikibot
.. image:: https://ci.appveyor.com/api/projects/status/xo2g4ctoom8k6yvw/branch/master?svg=true
   :alt: AppVeyor Build Status
   :target: https://ci.appveyor.com/project/ladsgroup/pywikibot-g4xqx
.. image:: https://codecov.io/gh/wikimedia/pywikibot/branch/master/graph/badge.svg
   :alt: Code coverage
   :target: https://codecov.io/gh/wikimedia/pywikibot
.. image:: https://api.codeclimate.com/v1/badges/de6ca4c66e7c7bee4156/maintainability
   :alt: Maintainability
   :target: https://codeclimate.com/github/wikimedia/pywikibot/maintainability
.. image:: https://img.shields.io/pypi/pyversions/pywikibot.svg
   :alt: Python
   :target: https://www.python.org/downloads/
.. image:: https://img.shields.io/pypi/v/pywikibot.svg
   :alt: Pywikibot release
   :target: https://pypi.org/project/pywikibot/

Pywikibot
=========

The Pywikibot framework is a Python library that interfaces with the
`MediaWiki API <https://www.mediawiki.org/wiki/API:Main_page>`_
version 1.14 or higher.

Also included are various general function scripts that can be adapted for
different tasks.

For further information about the library excluding scripts see
the full `code documentation <https://doc.wikimedia.org/pywikibot/>`_.

Quick start
-----------

::

    git clone https://gerrit.wikimedia.org/r/pywikibot/core.git
    cd core
    git submodule update --init
    python pwb.py script_name

Or to install using PyPI (excluding scripts)
::

    pip install -U setuptools
    pip install pywikibot

Our `installation
guide <https://www.mediawiki.org/wiki/Manual:Pywikibot/Installation>`_
has more details for advanced usage.

Basic Usage
-----------

If you wish to write your own script it's very easy to get started:

::

    import pywikibot
    site = pywikibot.Site('en', 'wikipedia')  # The site we want to run our bot on
    page = pywikibot.Page(site, 'Wikipedia:Sandbox')
    page.text = page.text.replace('foo', 'bar')
    page.save('Replacing "foo" with "bar"')  # Saves the page

-------------------------------------------------------------------------------------------

For more documentation on pywikibot see our `docs <https://doc.wikimedia.org/pywikibot/>`_.

.. include:: pywikibot/DIRECTORIES.rst

Required external programs
---------------------------

It may require the following programs to function properly:

* `7za`: To extract 7z files

.. include:: HISTORY.rst

Contributing
------------

Our code is maintained on Wikimedia's `Gerrit installation <https://gerrit.wikimedia.org/>`_,
`learn <https://www.mediawiki.org/wiki/Developer_account>`_ how to get
started.

.. include:: CODE_OF_CONDUCT.rst
