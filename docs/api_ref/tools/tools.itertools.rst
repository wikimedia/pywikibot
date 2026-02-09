**********************************************************
:mod:`tools.itertools` --- Iterators for Efficient Looping
**********************************************************

.. automodule:: tools.itertools
   :synopsis: Iterator functions

.. currentmodule:: tools.itertools
.. function:: itergroup(iterable, size: int, strict: bool = False) -> Generator[list[Any]]

   Make an iterator that returns lists of (up to) *size* items from *iterable*.

   .. versionadded:: 7.6
      The *strict* parameter.
   .. deprecated:: 8.2
      Use :func:`backports.batched` instead.
   .. versionremoved:: 11.0
      This function was removed; use :pylib:`itertools.batched<itertools#itertools.batched>` instead.
