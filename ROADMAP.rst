Current release changes
^^^^^^^^^^^^^^^^^^^^^^^

* Add support for dagwiki, shiwiki and banwikisource
* Fix and clean up DataSite.get_property_by_name
* Update handling of abusefilter-{disallow,warning} codes (T285317)
* Fix terminal_interface_base.input_list_choice (T285597)
* Fix ItemPage.fromPage call
* Use \*iterables instead of genlist in intersect_generators
* Use a sentinel variable to determine the end of an iterable in roundrobin_generators
* Require setuptools 20.8.1 (T284297)
* Add setter and deleter for summary_parameters of AutomaticTWSummaryBot
* L10N updates
* Add update_options attribute to BaseBot class to update available_options
* Clear put_queue when canceling page save (T284396)
* Add -url option to pagegenerators (T239436)
* Add add_text function to textlib (T284388)
* Require setuptools >= 49.4.0 (T284297)
* Require wikitextparser>=0.47.5
* Allow images to upload locally even they exist in the shared repository (T267535)
* Show a warning if pywikibot.__version__ is behind scripts.__version__ (T282766)
* Handle <ce>/<chem> tags as <math> aliases within textlib.replaceExcept() (T283990)
* Expand simulate query response for wikibase support (T76694)
* Double the wait time if ratelimit exceeded (T270912)
* Deprecated extract_templates_and_params_mwpfh and extract_templates_and_params_regex functions were removed

Deprecations
^^^^^^^^^^^^

* 6.4.0: Pywikibot `began using semantic versioning
  <https://www.mediawiki.org/wiki/Manual:Pywikibot/Development/Guidelines#Deprecation_Policy>`_,
  all deprecated code will be removed in Pywikibot version 7.0.0.
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
* 5.0.0: Methods deprecated for 5 years or longer will be removed
