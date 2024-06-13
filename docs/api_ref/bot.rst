****************************************
:mod:`bot` --- Classes for Building Bots
****************************************

.. automodule:: bot
   :synopsis: User-interface related functions for building bots
   :member-order: bysource

   .. admonition:: Imports in :mod:`pywikibot` module
      :class: note

      The following classes and functions are inported in :mod:`pywikibot`
      module and can also be used as :mod:`pywikibot` members:

      - :class:`pywikibot.Bot<bot.Bot>`
      - :class:`pywikibot.CurrentPageBot<bot.CurrentPageBot>`
      - :class:`pywikibot.WikidataBot<bot.WikidataBot>`
      - :func:`pywikibot.calledModuleName<bot.calledModuleName>`
      - :func:`pywikibot.handle_args<bot.handle_args>`
      - :func:`pywikibot.input<bot.input>`
      - :func:`pywikibot.input_choice<bot.input_choice>`
      - :func:`pywikibot.input_yn<bot.input_yn>`
      - :func:`pywikibot.show_help<bot.show_help>`

   .. autoclass:: BaseBot

      .. attribute:: generator
         :type: Iterable

         Instance variable to hold the Iterbale processed by :meth:`run`
         method. The is added to the class with *generator* keyword
         argument and the proposed type is a ``Generator``. If not,
         :meth:`run` upcast the generator attribute to become a
         ``Generator`` type. If a :class:`BaseBot` subclass has its own
         ``generator`` attribute, a warning will be thrown when an
         object is passed to *generator* keyword parameter.

         .. warning:: this is just a sample
