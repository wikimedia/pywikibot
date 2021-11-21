Current release changes
^^^^^^^^^^^^^^^^^^^^^^^

Improvements and Bugfixes
-------------------------

* Make pwb wrapper script a pywikibot entry point for scripts (T139143, T270480)
* Enable -version and --version with pwb wrapper or code entry point (T101828)
* Retry upload if 'copyuploadbaddomain' API error occurs (T294825)
* Add `title_delimiter_and_aliases` attribute to family files to support WikiHow family (T294761)
* Only handle query limit if query module is limited (T294836)
* BaseBot has a public collections.Counter for reading, writing and skipping a page
* Upload: Retry upload if 'copyuploadbaddomain' API error occurs (T294825)
* Upload: Only set filekey/offset for files with names (T294916)
* Update invisible characters from unicodedata 14.0.0
* Make site parameter of textlib.replace_links() mandatory (T294649)
* Raise a generic ServerError if the http status code is unofficial (T293208)
* Add support for Wikimedia OCR engine with proofreadpage
* Rewrite tools.intersect_generators which makes it running up to 10'000 times faster. (T85623, T293276)
* The cached output functionality from compat release was re-implemented (T151727, T73646, T74942, T132135, T144698, T196039, T280466)
* L10N updates
* Adjust groupsize within pagegenerators.PreloadingGenerator (T291770)
* New "maxlimit" property was added to APISite (T291770)


Breaking changes
----------------

* Support of Python 3.5.0 - 3.5.2 has been dropped (T286867)


Code cleanups
-------------

* Raise a TypeError if BaseBot.init_page return None
* Remove private upload parameters in UploadRobot.upload_file(), FilePage.upload() and APISite.upload() methods
* Raise an Error exception if 'titles' is still used as where parameter in Site.search()
* Deprecated version.get_module_version() function was removed
* Deprecated setOptions/getOptions OptionHandler methods were removed
* Deprecated from_page() method of CosmeticChangesToolkit was removed
* Deprecated diff attribute of CosmeticChangesToolkit  was removed in favour of show_diff
* Deprecated namespace and pageTitle parameter of CosmeticChangesToolkit were removed
* Remove deprecated BaseSite namespace shortcuts
* Remove deprecated Family.get_cr_templates method in favour of Site.category_redirects()
* Remove deprecated Page.put_async() method (T193494)
* Ignore baserevid parameter for several DataSite methods
* Remove deprecated preloaditempages method
* Remove disable_ssl_certificate_validation kwargs in http functions in favour of verify parameter (T265206)
* Deprecated PYWIKIBOT2 environment variables were removed
* version.ParseError was removed in favour of exceptions.VersionParseError
* specialbots.EditReplacement and specialbots.EditReplacementError were removed in favour of exceptions.EditReplacementError
* site.PageInUse exception was removed in favour of exceptions.PageInUseError
* page.UnicodeToAsciiHtml and page.unicode2html were removed in favour of tools.chars.string_to_ascii_html and tools.chars.string2html
* interwiki_graph.GraphImpossible and login.OAuthImpossible exception were removed in favour of ImportError
* i18n.TranslationError was removed in favour of exceptions.TranslationError
* WikiaFamily was removed in favour of FandomFamily
* data.api exceptions were removed in favour of exceptions module
* cosmetic_changes CANCEL_ALL/PAGE/METHOD/MATCH constants were removed in favour of CANCEL enum
* pywikibot.__release__ was removed in favour of pywikibot.__version__
* TextfilePageGenerator was replaced by TextIOPageGenerator
* PreloadingItemGenerator was replaced by PreloadingEntityGenerator
* DuplicateFilterPageGenerator was replaced by tools.filter_unique
* ItemPage.concept_url method was replaced by ItemPage.concept_uri
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

* 7.0.0: Private BaseBot counters _treat_counter, _save_counter, _skip_counter will be removed in favour of collections.Counter counter attribute
* 7.0.0: A boolean watch parameter in Page.save() is deprecated and will be desupported
* 7.0.0: baserevid parameter of editSource(), editQualifier(), removeClaims(), removeSources(), remove_qualifiers() DataSite methods will be removed
* 7.0.0: Values of APISite.allpages() parameter filterredir other than True, False and None are deprecated
* 6.5.0: OutputOption.output() method will be removed in favour of OutputOption.out property
* 6.4.0: Pywikibot `began using semantic versioning
  <https://www.mediawiki.org/wiki/Manual:Pywikibot/Development/Guidelines#Deprecation_Policy>`_,
  all deprecated code will be removed in Pywikibot version 7.0.0.
