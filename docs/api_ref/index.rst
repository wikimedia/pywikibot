#############
API reference
#############

****************************
High-level request structure
****************************

User code mainly interacts with :class:`pywikibot.Page` objects, which represent
pages on a specific wiki. These objects get their properties by calling functions
on their associated :class:`pywikibot.Site` object, which represents a specific
wiki.

The :class:`pywikibot.Site` object then calls the MediaWiki API using the
functions provided by :mod:`data.api`. This layer then uses :func:`comms.http.request`
to do the actual HTTP request.

*****************
Table of contents
*****************

.. toctree::
   :glob:
   :maxdepth: 2

   pywikibot
   pywikibot.config
   pywikibot.page
   proofreadpage
   pywikibot.pagegenerators
   pywikibot.site
   login
   logentries
   family
   pywikibot.families
   pywikibot.data
   pywikibot.comms
   exceptions
   textlib
   cosmetic_changes
   bot
   pywikibot.specialbots
   bot_choice
   pywikibot.userinterfaces
   logging
   *
