Current release changes
^^^^^^^^^^^^^^^^^^^^^^^

Improvements and Bugfixes
-------------------------

* The cached output functionality from compat release was re-implemented (T151727, T73646, T74942, T132135, T144698, T196039, T280466)
* Adjust groupsize within pagegenerators.PreloadingGenerator (T291770)
* New "maxlimit" property was added to APISite (T291770)


Breaking changes
----------------

* Support of Python 3.5.0 - 3.5.2 has been dropped (T286867)


Code cleanups
-------------

* Outdated parameter names has been dropped
* Deprecated pywikibot.Error exception were removed in favour of pywikibot.exceptions.Error classes (T280227)
* Deprecated exception identifiers were removed (T280227)
* Deprecated date.FormatDate class was removed in favour of date.format_date function
* language_by_size property of wowwiki Family was removed in favour of codes attribute
* availableOptions was removed in favour of available_options
* config2 was removed in favour of config
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

* 7.0.0: Values of APISite.allpages() parameter filterredir other than True, False and None are deprecated
* 6.5.0: OutputOption.output() method will be removed in favour of OutputOption.out property
* 6.4.0: Pywikibot `began using semantic versioning
  <https://www.mediawiki.org/wiki/Manual:Pywikibot/Development/Guidelines#Deprecation_Policy>`_,
  all deprecated code will be removed in Pywikibot version 7.0.0.
* 5.0.0: Methods deprecated for 5 years or longer will be removed
