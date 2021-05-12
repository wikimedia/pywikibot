Current release changes
~~~~~~~~~~~~~~~~~~~~~~~

* tools.is_IP was renamed to is_ip_address due to PEP8
* Fix Page.getDeletedRevision() method which always returned an empty list
* Async chunked uploads are supported (T129216, 133443)
* A new InvalidPageError will be raised if a Page has no version history (T280043)
* config2.py was renamed to config.py
* L10N updates
* Fix __getattr__ for WikibaseEntity (T281389)
* Handle abusefilter-{disallow,warning} codes (T85656)
* Exceptions were renamed having a suffix "Error" due to PEP8 (T280227)

Deprecations
~~~~~~~~~~~~

* 6.2.0: deprecated tools.is_IP will be removed
* 6.2.0: Usage of pywikibot.config2 is deprecated and will be dropped
* 6.2.0: Exceptions must be imported from exceptions namespace (T280227)
* 6.2.0: Deprecated exception identifiers will be removed (T280227)
* 6.2.0: empty_iterator will be removed in favour of iter()
* 6.1.0: tools.frozenmap will be removed in favour of types.MappingProxyType
* 6.1.0: tools.DotReadableDict will be removed
* 6.1.0: mwparserfromhell or wikitextparser MediaWiki markup parser becomes mandatory (T106763)
* 6.1.0: textlib.unescape() function will be removed in favour of html.unescape()
* 6.0.1: Site.undeletepage() and Site.undelete_file_versions() will be removed in favour of Site.undelete() method
* 6.0.1: Site.deletepage() and Site.deleteoldimage() will be removed in favour of Site.delete() method
* 6.0.1: DataSite.createNewItemFromPage() method will be removed in favour of ImagePage.fromPage() (T98663)
* 6.0.0: User.name() method will be removed in favour of User.username property
* 5.6.0: pagenenerators.handleArg() method will be removed in favour of handle_arg() (T271437)
* 5.6.0: Family.ignore_certificate_error() method will be removed in favour of verify_SSL_certificate() (T265205)
* 5.0.0: OptionHandler.options dict will be removed in favour of OptionHandler.opt
* 5.0.0: Methods deprecated for 5 years or longer will be removed
* 5.0.0: pagegenerators.ReferringPageGenerator is desupported and will be removed
