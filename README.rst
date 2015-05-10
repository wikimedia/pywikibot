Pywikibot
=========

The Pywikibot framework is a Python library that interfaces with the
`MediaWiki API <https://www.mediawiki.org/wiki/Special:MyLanguage/API:Main_page>`_
version 1.14 or higher.

Also included are various general function scripts that can be adapted for
different tasks.

Quick start
-----------

::

    git clone https://gerrit.wikimedia.org/r/pywikibot/core.git
    cd core
    git submodule update --init
    python pwb.py script_name

Our `installation
guide <https://www.mediawiki.org/wiki/Special:MyLanguage/Manual:Pywikibot/Installation>`_
has more details for advanced usage.

Usage
-----

If you wish to write your own script it's very easy to get started:

::

    import pywikibot
    site = pywikibot.Site('en', 'wikipedia')  # The site we want to run our bot on
    page = pywikibot.Page(site, 'Wikipedia:Sandbox')
    page.text = page.text.replace('foo', 'bar')
    page.save('Replacing "foo" with "bar"')  # Saves the page

Required external programms
---------------------------

It may require the following programs to function properly:

* `7za`: To extract 7z files

Contributing
------------

Our code is maintained on Wikimedia's `Gerrit installation <https://gerrit.wikimedia.org/>`_,
`learn <https://www.mediawiki.org/wiki/Special:MyLanguage/Developer_access>`_ how to get
started.

.. image:: https://secure.travis-ci.org/wikimedia/pywikibot-core.png?branch=master
   :alt: Build Status
   :target: https://travis-ci.org/wikimedia/pywikibot-core
