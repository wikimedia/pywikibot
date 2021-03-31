Current release changes
^^^^^^^^^^^^^^^^^^^^^^^

* mwparserfromhell or wikitextparser MediaWiki markup parser is mandatory (T106763)

Deprecations
^^^^^^^^^^^^

* 6.2.0: Bot's availableOptions will be removed in favour of available_options
* 6.2.0: deprecated tools.is_IP will be removed
* 6.2.0: Usage of pywikibot.config2 is deprecated and will be dropped
* 6.2.0: Exceptions must be imported from exceptions namespace (T280227)
* 6.2.0: Deprecated exception identifiers will be removed (T280227)
* 6.2.0: empty_iterator will be removed in favour of iter()
* 6.1.0: tools.frozenmap will be removed in favour of types.MappingProxyType
* 6.1.0: tools.DotReadableDict will be removed
* 6.1.0: textlib.unescape() function will be removed in favour of html.unescape()
* 6.0.1: Site.undeletepage() and Site.undelete_file_versions() will be removed in favour of Site.undelete() method
* 6.0.1: Site.deletepage() and Site.deleteoldimage() will be removed in favour of Site.delete() method
* 6.0.1: DataSite.createNewItemFromPage() method will be removed in favour of ImagePage.fromPage() (T98663)
* 5.0.0: Methods deprecated for 5 years or longer will be removed
