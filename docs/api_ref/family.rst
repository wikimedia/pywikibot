************************************
:mod:`family` --- MediaWiki families
************************************

.. automodule:: family
   :synopsis: Objects representing MediaWiki families

   .. autoclass:: Family

      .. method:: __init__()

         Initializer

         .. deprecated:: 3.0.20180710
            Use :meth:`__post_init__` instead.
         .. versionchanged:: 8.3
            A FutureWarning is printed instead of a ``NotImplementedWarning``.
            The deprecation may be removed in a future release and a
            ``RuntimeError`` will be thrown instead.

      .. method:: __post_init__()
         :classmethod:

         Post-init processing for Family class.

         The allocator will call this class method after the Family class was
         created and no :meth:`__init__()` method is used and ``__post_init__()``
         is defined in your Family subclass. This can be used for example to
         expand Family attribute lists.

         .. warning:: The ``__post_init__()`` classmethod cannot be inherited
            from a superclass. The current family file class is considered
            only.

         .. caution:: Never modify the current attributes directly; always use
            a copy. Otherwise the base class is modified which leads to
            unwanted side-effects.

         **Example:**

         .. code-block:: Python

            @classmethod
            def __post_init__(cls):
                """Add 'yue' code alias."""
                aliases = cls.code_aliases.copy()
                aliases['yue'] = 'zh-yue'
                cls.code_aliases = aliases

         .. versionadded:: 8.3

