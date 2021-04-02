Pywikibot Documentation
=======================

Welcome! This is the documentation for Pywikibot |release|.

.. note::

    This documentation is incomplete, and needs quite some work.

    If you are not familiar with Pywikibot, please start at the
    documentation:

    `Manual:Pywikibot on mediawiki.org <https://www.mediawiki.org/wiki/Manual:Pywikibot>`_

**Pywikibot** is a Python library and collection of tools that automate work
on `MediaWiki <https://mediawiki.org>`_ sites. Originally designed for 
Wikipedia, it is now used throughout the Wikimedia Foundation's projects and
on many other MediaWiki wikis.

The project started in 2003 and is currently on core version |version|.
It features full API usage and is up-to-date with new MediaWiki features and
a Pythonic package layout. But it also works with older installations of 
MediaWiki 1.23 or higher.

Pywikibot supports Microsoft Windows, macOS and Linux when used with a 
compatible version of Python. It should also work on any other operating
system that has a compatible version of Python installed. To check 
whether you have Python installed and to find its version, just type
``python`` at the CMD or shell prompt.

Python 3.5 or higher is currently required to run the bot, but Python 3.6
or higher is recommended.

Pywikibot and this documentation are licensed under the
:ref:`MIT license <licenses-MIT>`;
manual pages on mediawiki.org are licensed under the `CC-BY-SA 3.0`_ license.

The documentation consists of four major parts:

#. :doc:`installation`
#. :doc:`scripts/index`
#. :doc:`library_usage`
#. :doc:`api_ref/index`

For bot users:
==============

.. toctree::
   :maxdepth: 1

   installation
   scripts/index
   getting_help


For bot developers:
===================

.. toctree::
   :maxdepth: 2

   installation
   library_usage
   getting_help
   api_ref/index

For framework developers:
=========================

.. toctree::
   :maxdepth: 1

   scripts/scripts.maintenance


Miscellaneous
=============
.. toctree::

   licenses
   credits


.. _CC-BY-SA 3.0: http://creativecommons.org/licenses/by-sa/3.0/
