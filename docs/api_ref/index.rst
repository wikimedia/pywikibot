API reference
-------------

High-level request structure
============================

User code mainly interacts with :class:`pywikibot.Page` objects, which represent
pages on a specific wiki. These objects get their properties by calling functions
on their associated :class:`pywikibot.Site` object, which represents a specific
wiki.

The :class:`pywikibot.Site` object then calls the MediaWiki API using the
functions provided by :mod:`pywikibot.data.api`. This layer then uses :func:`pywikibot.comms.http.request`
to do the actual HTTP request.

Contents
========

.. toctree::
   :glob:

   *

Test documentation
==================
#. :doc:`tests/index`

