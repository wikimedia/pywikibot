Current release changes
^^^^^^^^^^^^^^^^^^^^^^^

Breaking changes
----------------

* Support of Python 3.5.0 - 3.5.2 has been dropped (T286867)


Code cleanups
-------------

* tools.RotatingFileHandler was removed in favour of logging.handlers.RotatingFileHandler
* tools.DotReadableDict, tools.LazyRegex and tools.DeprecatedRegex classes were removed
* tools.frozenmap was removed in favour of types.MappingProxyType
* tools.empty_iterator() was removed in favour of iter(())
* tools.concat_options() function was removed in favour of bot_choice.Option
* tools.is_IP was be removed in favour of tools.is_ip_address()
* textlib.unescape() function was be removed in favour of html.unescape()
* APISite.deletepage() and APISite.deleteoldimage() methods were removed in favour of APISite.delete() 
* APISite.undeletepage() and APISite.undelete_file_versions() were be removed in favour of APISite.undelete() method


Deprecations
^^^^^^^^^^^^

* 6.5.0: OutputOption.output() method will be removed in favour of OutputOption.out property
* 6.4.0: Pywikibot `began using semantic versioning
  <https://www.mediawiki.org/wiki/Manual:Pywikibot/Development/Guidelines#Deprecation_Policy>`_,
  all deprecated code will be removed in Pywikibot version 7.0.0.
* 6.2.0: Bot's availableOptions will be removed in favour of available_options
* 6.2.0: Usage of pywikibot.config2 is deprecated and will be dropped
* 6.2.0: Exceptions must be imported from exceptions namespace (T280227)
* 6.2.0: Deprecated exception identifiers will be removed (T280227)
* 5.0.0: Methods deprecated for 5 years or longer will be removed
