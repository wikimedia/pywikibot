****************************************
:mod:`bot` --- Classes for Building Bots
****************************************

.. automodule:: bot
   :synopsis: User-interface related functions for building bots
   :member-order: bysource

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
