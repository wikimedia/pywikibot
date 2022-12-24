********
Glossary
********

.. if you add new entries, keep the alphabetical sorting!

.. glossary::

   ``>>>``
      The default Python prompt of the interactive Pywikibot shell.
      Often seen for code examples which can be executed interactively
      in the interpreter. The :mod:`pywikibot` module is preloaded. The
      :mod:`pywikibot.scripts.shell` script is part of the
      :ref:`Pywikibot Utility Scripts<Utility Scripts>`.

   compat
      The first Pywikibot package formerly known as *Pywikipediabot*
      also called :term:`trunk` was started in 2003. MediaWiki didn't
      have an API so a `screen scrapping
      <https://en.wikipedia.org/wiki/Screen_scraper>`_ was used.

   core
      In 2007 a new branch of Pywikibot formerly known as
      :term:`trunk` was started using the new MediaWiki API. The
      current release is |release|.

   master
      The development branch of Pywikibot. It should not be used for
      production systems, use :term:`stable` instead. The master branch
      may have untested features. Use master branch if you want to
      support development and report undetected problems.

   pwb
      Can refer to:

      - short for Pywikibot
      - the :mod:`pwb` wrapper script

   python2
      A :term:`tag` for the last Pywikibot release :ref:`3.0.20200703`
      supporting Python 2 (Python 2.7.3 - 2.7.18). Ask for :phab:`Python 2 to
      3 support <T242120>` to convert your old scripts.

   pywikibot
      **Py**\ thon Media\ **Wiki Bot** Framework, a Python library and
      collection of scripts that automate work on MediaWiki sites.
      Originally designed for Wikipedia, it is now used throughout the
      Wikimedia Foundation's projects and on many other wikis based of
      MediaWiki software.

   rewrite
      A former name of :term:`core`.

   stable
      A stable branch of Pywikibot updated roughly every month
      after tests passes. This branch is preinstalled at :term:`PAWS`
      and should be used for production systems.

   tag
      A marker of particular revisions (e.g. a release version). Each
      Pywikibot release is tagged with its release version number. The
      current last tag is |version|.

   trunk
      A former name of :term:`compat`.

   PAWS
      PAWS (PAWS: A Web Shell) formerly known as *Pywikibot: A Web Shell*
      is a Jupyter notebooks deployment hosted by Wikimedia. It has
      preinstalled the :term:`stable` release of Pywikibot. Refer:

      - :manpage:`PAWS`
      - https://wikitech.wikimedia.org/wiki/PAWS

   PyPI
      The Python Package Index (PyPI), a repository of software for the
      Python programming language. Pywikibot framework (without scripts)
      is `published monthly at PyPI
      <https://pypi.org/project/pywikibot/>`_.
