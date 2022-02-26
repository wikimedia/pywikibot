Current release changes
^^^^^^^^^^^^^^^^^^^^^^^

Improvements
------------

* i18n updates for date.py
* Add number transliteration of 'lo', 'ml', 'pa', 'te' to NON_LATIN_DIGITS
* Detect range blocks with Page.is_blocked() method (T301282)
* to_latin_digits() function was added to textlib as counterpart of to_local_digits() function
* api.Request.submit now handles search-title-disabled and search-text-disabled API Errors
* A show_diff parameter  was added to Page.put() and Page.change_category()
* Allow categories when saving IndexPage (T299806)
* Add a new function case_escape to textlib
* Support inheritance of the __STATICREDIRECT__
* Avoid non-deteministic behavior in removeDisableParts
* Update isbn dependency and require python-stdnum >= 1.17
* Synchronize Page.linkedPages() parameters with Site.pagelinks() parameters
* Scripts hash bang was changed from python to python3
* i18n.bundles(), i18n.known_languages and  i18n._get_bundle() functions were added
* Raise ConnectionError immediately if urllib3.NewConnectionError occurs (T297994, 298859)
* Make pywikibot messages available with site package (T57109, T275981)
* Add support for API:Redirects
* Enable shell script with Pywikibot site package
* Enable generate_user_files.py and generate_family_file with site-package (T107629)
* Add support for Python 3.11
* Pywikibot supports PyPy 3 (T101592)
* A new method User.is_locked() was added to determine whether the user is currently locked globally (T249392)
* A new method APISite.is_locked() was added to determine whether a given user or user id is locked globally (T249392)
* APISite.get_globaluserinfo() method was added to retrieve globaluserinfo for any user or user id (T163629)
* APISite.globaluserinfo attribute may be deleted to force reload
* APISite.is_blocked() method has a force parameter to reload that info
* Allow family files in base_dir by default
* Make pwb wrapper script a pywikibot entry point for scripts (T139143, T270480)
* Enable -version and --version with pwb wrapper or code entry point (T101828)
* Add `title_delimiter_and_aliases` attribute to family files to support WikiHow family (T294761)
* BaseBot has a public collections.Counter for reading, writing and skipping a page
* Upload: Retry upload if 'copyuploadbaddomain' API error occurs (T294825)
* Update invisible characters from unicodedata 14.0.0
* Add support for Wikimedia OCR engine with proofreadpage
* Rewrite tools.intersect_generators which makes it running up to 10'000 times faster. (T85623, T293276)
* The cached output functionality from compat release was re-implemented (T151727, T73646, T74942, T132135, T144698, T196039, T280466)
* L10N updates
* Adjust groupsize within pagegenerators.PreloadingGenerator (T291770)
* New "maxlimit" property was added to APISite (T291770)


Bugfixes
--------

* Don't raise an exception if BlockEntry initializer found a hidden title (T78152)
* Fix KeyError in create_warnings_list (T301610)
* Enable similar script call of pwb.py on toolforge (T298846)
* Remove question mark character from forbidden file name characters (T93482)
* Enable -interwiki option with pagegenerators (T57099)
* Don't assert login result (T298761)
* Allow title placeholder $1 in the middle of an url (T111513, T298078)
* Don't create a Site object if pywikibot is not fully imported (T298384)
* Use page.site.data_repository when creating a _WbDataPage (T296985)
* Fix mysql AttributeError for sock.close() on toolforge (T216741)
* Only search user_script_paths inside config.base_dir (T296204)
* pywikibot.argv has been fixed for pwb.py wrapper if called with global args (T254435)
* Only ignore FileExistsError when creating the api cache (T295924)
* Only handle query limit if query module is limited (T294836)
* Upload: Only set filekey/offset for files with names (T294916)
* Make site parameter of textlib.replace_links() mandatory (T294649)
* Raise a generic ServerError if the http status code is unofficial (T293208)


Breaking changes
----------------

* Support of Python 3.5.0 - 3.5.2 has been dropped (T286867)
* generate_user_files.py, generate_user_files.py, shell.py and version.py were moved to pywikibot/scripts and must be used with pwb wrapper script
* *See also Code cleanups below*


Code cleanups
-------------

* Deprecated  http.get_fake_user_agent() function was removed
* FilePage.fileIsShared() was removed in favour of FilePage.file_is_shared()
* Page.canBeEdited() was removed in favour of Page.has_permission()
* BaseBot.stop() method were removed in favour of BaseBot.generator.close()
* showHelp() function was remove in favour of show_help
* CombinedPageGenerator pagegenerator was removed in favour of itertools.chain
* Remove deprecated echo.Notification.id
* Remove APISite.newfiles() method (T168339)
* Remove APISite.page_exists() method
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

* 7.0.0: The i18n identifier 'cosmetic_changes-append' will be removed in favour of 'pywikibot-cosmetic-changes'
* 7.0.0: User.isBlocked() method is renamed to is_blocked for consistency
* 7.0.0: Require mysql >= 0.7.11 (T216741)
* 7.0.0: Private BaseBot counters _treat_counter, _save_counter, _skip_counter will be removed in favour of collections.Counter counter attribute
* 7.0.0: A boolean watch parameter in Page.save() is deprecated and will be desupported
* 7.0.0: baserevid parameter of editSource(), editQualifier(), removeClaims(), removeSources(), remove_qualifiers() DataSite methods will be removed
* 7.0.0: Values of APISite.allpages() parameter filterredir other than True, False and None are deprecated
* 6.5.0: OutputOption.output() method will be removed in favour of OutputOption.out property
* 6.5.0: Infinite rotating file handler with logfilecount of -1 is deprecated
* 6.4.0: 'allow_duplicates' parameter of tools.intersect_generators as positional argument is deprecated, use keyword argument instead
* 6.4.0: 'iterables' of tools.intersect_generators given as a list or tuple is deprecated, either use consecutive iterables or use '*' to unpack
* 6.2.0: outputter of OutputProxyOption without out property is deprecated
* 6.2.0: ContextOption.output_range() and HighlightContextOption.output_range() are deprecated
* 6.2.0: Error messages with '%' style is deprecated in favour for str.format() style
* 6.2.0: page.url2unicode() function is deprecated in favour of tools.chars.url2string()
* 6.2.0: Throttle.multiplydelay attribute is deprecated
* 6.2.0: SequenceOutputter.format_list() is deprecated in favour of 'out' property
* 6.0.0: config.register_family_file() is deprecated
* 5.5.0: APISite.redirectRegex() is deprecated in favour of APISite.redirect_regex()
* 4.0.0: Revision.parent_id is deprecated in favour of Revision.parentid
* 4.0.0: Revision.content_model is deprecated in favour of Revision.contentmodel

