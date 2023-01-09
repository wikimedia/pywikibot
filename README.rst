.. image:: https://github.com/wikimedia/pywikibot/actions/workflows/pywikibot-ci.yml/badge.svg?branch=master
   :alt: GitHub CI
   :target: https://github.com/wikimedia/pywikibot/actions/workflows/pywikibot-ci.yml
.. image:: https://ci.appveyor.com/api/projects/status/xo2g4ctoom8k6yvw/branch/master?svg=true
   :alt: AppVeyor Build Status
   :target: https://ci.appveyor.com/project/pywikibot-core/pywikibot
.. image:: https://codecov.io/gh/wikimedia/pywikibot/branch/master/graph/badge.svg
   :alt: Code coverage
   :target: https://app.codecov.io/gh/wikimedia/pywikibot
.. image:: https://api.codeclimate.com/v1/badges/de6ca4c66e7c7bee4156/maintainability
   :alt: Maintainability
   :target: https://codeclimate.com/github/wikimedia/pywikibot
.. image:: https://img.shields.io/pypi/pyversions/pywikibot.svg
   :alt: Python
   :target: https://www.python.org/downloads/
.. image:: https://img.shields.io/github/languages/top/wikimedia/pywikibot
   :alt: Top language
   :target: https://www.python.org/downloads/
.. image:: https://img.shields.io/pypi/v/pywikibot.svg
   :alt: Pywikibot release
   :target: https://pypi.org/project/pywikibot/
.. image:: https://img.shields.io/pypi/wheel/pywikibot
   :alt: wheel
   :target: https://pypi.org/project/pywikibot/
.. image:: https://static.pepy.tech/badge/pywikibot
   :alt: Total downloads
   :target: https://pepy.tech/project/pywikibot
.. image:: https://static.pepy.tech/personalized-badge/pywikibot?period=month&units=international_system&left_color=black&right_color=blue&left_text=monthly
   :alt: Monthly downloads
   :target: https://pepy.tech/project/pywikibot
.. image:: https://img.shields.io/github/last-commit/wikimedia/pywikibot
   :alt: Last commit
   :target: https://gerrit.wikimedia.org/r/plugins/gitiles/pywikibot/core/

*********
Pywikibot
*********

The Pywikibot framework is a Python library that interfaces with the
`MediaWiki API <https://www.mediawiki.org/wiki/API:Main_page>`_
version 1.27 or higher.

Also included are various general function scripts that can be adapted for
different tasks.

For further information about the library excluding scripts see
the full `code documentation <https://doc.wikimedia.org/pywikibot/>`_.

Quick start
===========

.. code:: text

    pip install requests
    git clone https://gerrit.wikimedia.org/r/pywikibot/core.git
    cd core
    git submodule update --init
    python pwb.py script_name

Or to install using PyPI (excluding scripts)

.. code:: text

    pip install -U setuptools
    pip install pywikibot
    pwb <scriptname>

Our `installation
guide <https://www.mediawiki.org/wiki/Manual:Pywikibot/Installation>`_
has more details for advanced usage.

Basic Usage
===========

If you wish to write your own script it's very easy to get started:

.. code:: python

    import pywikibot
    site = pywikibot.Site('en', 'wikipedia')  # The site we want to run our bot on
    page = pywikibot.Page(site, 'Wikipedia:Sandbox')
    page.text = page.text.replace('foo', 'bar')
    page.save('Replacing "foo" with "bar"')  # Saves the page

Wikibase Usage
==============

Wikibase is a flexible knowledge base software that drives Wikidata.
A sample pywikibot script for getting data from Wikibase:

.. code:: python

    import pywikibot
    site = pywikibot.Site('wikipedia:en')
    repo = site.data_repository()  # the Wikibase repository for given site
    page = repo.page_from_repository('Q91')  # create a local page for the given item
    item = pywikibot.ItemPage(repo, 'Q91')  # a repository item
    data = item.get()  # get all item data from repository for this item

Script example
==============

Pywikibot provides bot classes to develop your own script easily:

.. code:: python

    import pywikibot
    from pywikibot import pagegenerators
    from pywikibot.bot import ExistingPageBot

    class MyBot(ExistingPageBot):

        update_options = {
            'text': 'This is a test text',
            'summary': 'Bot: a bot test edit with Pywikibot.'
        }

        def treat_page(self):
            """Load the given page, do some changes, and save it."""
            text = self.current_page.text
            text += '\n' + self.opt.text
            self.put_current(text, summary=self.opt.summary)

    def main():
        """Parse command line arguments and invoke bot."""
        options = {}
        gen_factory = pagegenerators.GeneratorFactory()
        # Option parsing
        local_args = pywikibot.handle_args(args)  # global options
        local_args = gen_factory.handle_args(local_args)  # generators options
        for arg in local_args:
            opt, sep, value = arg.partition(':')
            if opt in ('-summary', '-text'):
                options[opt[1:]] = value
        MyBot(generator=gen_factory.getCombinedGenerator(), **options).run()

    if __name == '__main__':
        main()


For more documentation on Pywikibot see our `docs <https://doc.wikimedia.org/pywikibot/>`_.


Roadmap
=======

.. include:: ROADMAP.rst

Release history
===============

See https://github.com/wikimedia/pywikibot/blob/stable/HISTORY.rst

Contributing
============

Our code is maintained on Wikimedia's `Gerrit installation <https://gerrit.wikimedia.org/>`_,
`learn <https://www.mediawiki.org/wiki/Developer_account>`_ how to get
started.

.. include:: CODE_OF_CONDUCT.rst
