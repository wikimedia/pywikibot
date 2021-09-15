Release history
^^^^^^^^^^^^^^^

6.6.0
-----
*15 September 2021*

* Drop piprop from meta=proofreadinfo API call (T290585)
* Remove use_2to3 with setup.py (T290451)
* Unify WbRepresentation's abstract method signature
* L10N updates


6.5.0
-----
*05 August 2021*

* Add support for jvwikisource (T286247)
* Handle missingtitle error code when deleting
* Check for outdated setuptools in pwb.py wrapper (T286980)
* Remove traceback for original exception for known API error codes
* Unused strm parameter of init_handlers was removed
* Ignore throttle.pid if a Site object cannot be created (T286848)
* Explicitly return an empty string with OutputProxyOption.out property (T286403)
* Explicitly return None from ContextOption.result() (T286403)
* Add support for Lingua Libre family (T286303)
* Catch invalid titles in Category.isCategoryRedirect()
* L10N updates
* Provide structured data on Commons (T213904, T223820)


6.4.0
-----
*01 July 2021*

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


6.3.0
-----
*31 May 2021*

* Check bot/nobots templates for cosmetic_changes hook (T283989)
* Remove outdated opt._option which is already dropped (T284005)
* Use IntEnum with cosmetic_changes CANCEL
* Remove lru_cahce from botMayEdit method and fix it's logic (T283957)
* DataSite.createNewItemFromPage() method was removed in favour of ImagePage.fromPage() (T98663)
* mwparserfromhell or wikitextparser MediaWiki markup parser is mandatory (T106763)


6.2.0
-----
*28 May 2021*

Improvements and Bugfixes
~~~~~~~~~~~~~~~~~~~~~~~~~

* Use different logfiles for multiple processes of the same script (T56685)
* throttle.pip will be reused as soon as possbile
* terminal_interface_base.TerminalHandler is subclassed from logging.StreamHandler
* Fix iterating of SizedKeyCollection (T282865)
* An abstract base user interface module was added
* APISite method pagelanglinks() may skip links with empty titles (T223157)
* Fix Page.getDeletedRevision() method which always returned an empty list
* Async chunked uploads are supported (T129216, T133443)
* A new InvalidPageError will be raised if a Page has no version history (T280043)
* L10N updates
* Fix __getattr__ for WikibaseEntity (T281389)
* Handle abusefilter-{disallow,warning} codes (T85656)

Code cleanups
~~~~~~~~~~~~~

* MultipleSitesBot.site attribute was removed (T283209)
* Deprecated BaseSite.category_namespaces() method was removed
* i18n.twntranslate() function was removed in favour of twtranslate()
* siteinfo must be used as a dictionary ad cannot be called anymore
* APISite.has_transcluded_data() method was removed
* Deprecated LogEntry.title() method was removed
* Deprecated APISite.watchpage() method was removed
* OptionHandler.options dict has been removed in favour of OptionHandler.opt
* The toStdout parameter of ui.output has been dropped
* terminal_interface_base.TerminalFormatter was removed
* Move page functions UnicodeToAsciiHtml, unicode2html, url2unicode to tools.chars with renaming them
* Rename _MultiTemplateMatchBuilder to MultiTemplateMatchBuilder
* User.name() method was removed in favour of User.username property
* BasePage.getLatestEditors() method was removed in favour of contributors() or revisions()
* pagenenerators.handleArg() method was renamed to handle_arg() (T271437)
* CategoryGenerator, FileGenerator, ImageGenerator and ReferringPageGenerator pagegenerator functions were removed
* Family.ignore_certificate_error() method was removed in favour of verify_SSL_certificate (T265205)
* tools.is_IP was renamed to is_ip_address due to PEP8
* config2.py was renamed to config.py
* Exceptions were renamed having a suffix "Error" due to PEP8 (T280227)


6.1.0
-----
*17 April 2021*

Improvements and Bugfixes
~~~~~~~~~~~~~~~~~~~~~~~~~

* proofreadpage: search for "new" class after purge (T280357)
* Enable different types with BaseBot.treat()
* Context manager depends on pymysql version, not Python release (T279753)
* Bugfix for Site.interwiki_prefix() (T188179)
* Exclude expressions from parsed template in mwparserfromhell (T71384)
* Provide an object representation for DequeGenerator
* Allow deleting any subclass of BasePage by title (T278659)
* Add support for API:Revisiondelete with Site.deleterevs() method (T276726)
* L10N updates
* Family files can be collected from a zip folder (T278076)

Dependencies
~~~~~~~~~~~~

* **mwparserfromhell** or **wikitextparser** are strictly recommended (T106763)
* Require **Pillow**>=8.1.1 due to vulnerability found (T278743)
* TkDialog of GUI userinterface requires **Python 3.6+** (T278743)
* Enable textlib.extract_templates_and_params with **wikitextparser** package
* Add support for **PyMySQL** 1.0.0+

Code cleanups
~~~~~~~~~~~~~

* APISite.resolvemagicwords(), BaseSite.ns_index() and remove BaseSite.getNamespaceIndex() were removed
* Deprecated MoveEntry.new_ns() and new_title() methods were removed
* Unused NoSuchSite and PageNotSaved exception were removed
* Unused BadTitle exception was removed (T267768)
* getSite() function was removed in favour of Site() constructor
* Page.fileUrl() was removed in favour of Page.get_file_url()
* Deprecated getuserinfo and getglobaluserinfo Site methods were removed


6.0.1
-----
*20 March 2021*

* Add support for taywiki, trvwiki and mnwwiktionary (T275838, T276128, T276250)


6.0.0
-----
*16 March 2021*

Breaking changes
~~~~~~~~~~~~~~~~

* interwiki_graph module was removed (T223826)
* Require setuptools >= 20.2 due to PEP 440
* Support of MediaWiki < 1.23 has been dropped (T268979)
* APISite.loadimageinfo will no longer return any content
* Return requests.Response with http.request() instead of plain text (T265206)
* config.db_hostname has been renamed to db_hostname_format

Code cleanups
~~~~~~~~~~~~~

* tools.PY2 was removed (T213287)
* Site.language() method was removed in favour of Site.lang property
* Deprecated Page.getMovedTarget() method was removed in favour of moved_target()
* Remove deprecated Wikibase.lastrevid attribute
* config settings of archived scripts were removed (T223826)
* Drop startsort/endsort parameter for site.categorymembers method (T74101)
* Deprecated data attribute of http.fetch() result has been dropped (T265206)
* toStdout parameter of pywikibot.output() has been dropped
* Deprecated Site.getToken() and Site.case was removed
* Deprecated Family.known_families dict was removed (T89451)
* Deprecated DataSite.get_* methods was removed
* Deprecated LogEntryFactory.logtypes classproperty was removed
* Unused comms.threadedhttp module was removed; threadedhttp.HttpRequest was already replaced with requests.Response (T265206)

Other changes
~~~~~~~~~~~~~

* Raise a SiteDefinitionError if api request response is Non-JSON and site is AutoFamily (T272911)
* Support deleting and undeleting specific file versions (T276725)
* Only add bot option generator if the bot class have it already
* Raise a RuntimeError if pagegenerators -namespace option is provided too late (T276916)
* Check for LookupError exception in http._decide_encoding (T276715)
* Re-enable setting private family files (T270949)
* Move the hardcoded namespace identifiers to an IntEnum
* Buffer 'pageprops' in api.QueryGenerator
* Ensure that BaseBot.generator is a Generator
* Add additional info into log if 'messagecode' is missing during login (T261061, T269503)
* Use hardcoded messages if i18n system is not available (T275981)
* Move wikibase data structures to page/_collections.py
* L10N updates
* Add support for altwiki (T271984)
* Add support for mniwiki and mniwiktionary (T273467, T273462)
* Don't use mime parameter as boolean in api.Request (T274723)
* textlib.removeDisabledPart is able to remove templates (T274138)
* Create a SiteLink with __getitem__ method and implement lazy load (T273386, T245809, T238471, T226157)
* Fix date.formats['MonthName'] behaviour (T273573)
* Implement pagegenerators.handle_args() to process all options at once
* Add enabled_options, disabled_options to GeneratorFactory (T271320)
* Move interwiki() interwiki_prefix() and local_interwiki() methods from BaseSite to APISite
* Add requests.Response.headers to log when an API error occurs (T272325)


5.6.0
-----
*24 January 2021*

* Use string instead of Path-like object with "open" function in UploadRobot for Python 3.5 compatibility (T272345)
* Add support for trwikivoyage (T271263)
* UI.input_list_choice() has been improved (T272237)
* Global handleArgs() function was removed in favour of handle_args
* Deprecated originPage and foundIn property has been removed in interwiki_graph.py
* ParamInfo modules, prefixes, query_modules_with_limits properties and module_attribute_map() method was removed
* Allow querying alldeletedrevisions with APISite.alldeletedrevisions() and User.deleted_contributions()
* data attribute of http.fetch() response is deprecated (T265206)
* Positional arguments of page.Revision aren't supported any longer (T259428)
* pagenenerators.handleArg() method was renamed to handle_arg() (T271437)
* Page methods deprecated for 6 years were removed
* Create a Site with AutoFamily if a family isn't predefined (T249087)
* L10N updates


5.5.0
-----
*12 January 2021*

* Add support for niawiki, bclwikt, diqwikt, niawikt (T270416, T270282, T270278, T270412)
* Delete page using pageid instead of title (T57072)
* version.getversion_svn_setuptools function was removed (T270393)
* Add support for "musical notation" data type to wikibase
* -grepnot filter option was added to pagegenerators module (T219281)
* L10N updates


5.4.0
-----
*2 January 2021*

* Re-enable reading user-config.py from site package (T270941)
* LoginManager.getCookie() was renamed to login_to_site()
* Deprecation warning for MediaWiki < 1.23 (T268979)
* Add backports to support some Python 3.9 changes
* Desupported shared_image_repository() and nocapitalize() methods were removed (T89451)
* pywikibot.cookie_jar was removed in favour of pywikibot.comms.http.cookie_jar
* Align http.fetch() params with requests and rename 'disable_ssl_certificate_validation' to 'verify' (T265206)
* Deprecated compat BasePage.getRestrictions() method was removed
* Outdated Site.recentchanges() parameters has been dropped
* site.LoginStatus has been removed in favour of login.LoginStatus
* L10N Updates


5.3.0
-----
*19 December 2020*

* Allow using pywikibot as site-package without user-config.py (T270474)
* Python 3.10 is supported
* Fix AutoFamily scriptpath() call (T270370)
* Add support for skrwiki, skrwiktionary, eowikivoyage, wawikisource, madwiki (T268414, T268460, T269429, T269434, T269442)
* wikistats methods fetch, raw_cached, csv, xml has been removed
* PageRelatedError.getPage() has been removed in favour of PageRelatedError.page
* DataSite.get_item() method has been removed
* global put_throttle option may be given as float (T269741)
* Property.getType() method has been removed
* Family.server_time() method was removed; it is still available from Site object (T89451)
* All HttpRequest parameters except of charset has been dropped (T265206)
* A lot of methods and properties of HttpRequest are deprecared in favour of requests.Resonse attributes (T265206)
* Method and properties of HttpRequest are delegated to requests.Response object (T265206)
* comms.threadedhttp.HttpRequest.raw was replaced by HttpRequest.content property (T265206)
* Desupported version.getfileversion() has been removed
* site parameter of comms.http.requests() function is mandatory and cannot be omitted
* date.MakeParameter() function has been removed
* api.Request.http_params() method has been removed
* L10N updates


5.2.0
-----
*10 December 2020*

* Remove deprecated args for Page.protect() (T227610)
* Move BaseSite its own site/_basesite.py file
* Improve toJSON() methods in page.__init__.py
* _is_wikibase_error_retryable rewritten (T48535, 268645)
* Replace FrozenDict with frozenmap
* WikiStats table may be sorted by any key
* Retrieve month names from mediawiki_messages when required
* Move Namespace and NamespacesDict to site/_namespace.py file
* Fix TypeError in api.LoginManager (T268445)
* Add repr() method to BaseDataDict and ClaimCollection
* Define availableOptions as deprecated property
* Do not strip all whitespaces from Link.title (T197642)
* Introduce a common BaseDataDict as parent for LanguageDict and AliasesDict
* Replaced PageNotSaved by PageSaveRelatedError (T267821)
* Add -site option as -family -lang shortcut
* Enable APISite.exturlusage() with default parameters (T266989)
* Update tools._unidata._category_cf from Unicode version 13.0.0
* Move TokenWallet to site/_tokenwallet.py file
* Fix import of httplib after release of requests 2.25 (T267762)
* user keyword parameter can be passed to Site.rollbackpage() (T106646)
* Check for {{bots}}/{{nobots}} templates in Page.text setter (T262136, T267770)
* Remove deprecated UserBlocked exception and Page.contributingUsers()
* Add support for some 'wbset' actions in DataSite
* Fix UploadRobot site attribute (T267573)
* Ignore UnicodeDecodeError on input (T258143)
* Replace 'source' exception regex with 'syntaxhighlight' (T257899)
* Fix get_known_families() for wikipedia_family (T267196)
* Move _InterwikiMap class to site/_interwikimap.py
* instantiate a CosmeticChangesToolkit by passing a page
* Create a Site from sitename
* pywikibot.Site() parameters "interface" and "url" must be keyworded
* Lookup the code parameter in xdict first (T255917)
* Remove interwiki_forwarded_from list from family files (T104125)
* Rewrite Revision class; each data can be accessed either by key or as an attribute (T102735, T259428)
* L10N-Updates


5.1.0
-----

*1 November 2020*

* Avoid conflicts between site and possible site keyword in api.Request.create_simple() (T262926)
* Remove wrong param of rvision() call in Page.latest_revision_id
* Do not raise Exception in Page.get_best_claim() but follow redirect (T265839)
* xml-support of wikistats will be dropped
* Remove deprecated mime_params in api.Request()
* cleanup interwiki_graph.py and replace deprecated originPage by origin in Subjects
* Upload a file that ends with the '\r' byte (T132676)
* Fix incorrect server time (T266084)
* L10N-Updates
* Support Namespace packages in version.py (T265946)
* Server414Error was added to pywikibot (T266000)
* Deprecated editor.command() method was removed
* comms.PywikibotCookieJar and comms.mode_check_decorator were deleted
* Remove deprecated tools classes Stringtypes and UnicodeType
* Remove deprecated tools function open_compressed and signature and UnicodeType class
* Fix http_tests.LiveFakeUserAgentTestCase (T265842)
* HttpRequest properties were renamed to request.Response identifiers (T265206)


5.0.0
-----

*19 October 2020*

* Add support for smn-wiki (T264962)
* callback parameter of comms.http.fetch() is desupported
* Fix api.APIError() calls for Flow and Thanks extension
* edit, move, create, upload, unprotect and prompt parameters of Page.protect() are deprecated (T227610)
* Accept only valid names in generate_family_file.py (T265328, T265353)
* New plural.plural_rule() function returns a rule for a given language
* Replace deprecated urllib.request.URLopener with http.fetch (T255575)
* OptionHandler/BaseBot options are accessable as OptionHandler.opt attributes or keyword item (see also T264721)
* pywikibot.setAction() function was removed
* A namedtuple is the result of textlib.extract_sections()
* Prevent circular imports in config2.py and http.py (T264500)
* version.get_module_version() is deprecated and gives no meaningfull result
* Fix version.get_module_filename() and update log lines (T264235)
* Re-enable printing log header (T264235)
* Fix result of tools.intersect_generators() (T263947)
* Only show _GLOBAL_HELP options if explicitly wanted
* Deprecated Family.version() methods were removed
* Unused parameters of page methods like forceReload, insite, throttle, step was removed
* Raise RuntimeError instead of AttributeError for old wikis (T263951)
* Deprecated script options were removed
* lyricwiki_family was removed (T245439)
* RecentChangesPageGenerator parameters has been synced with APISite.recentchanges
* APISite.recentchanges accepts keyword parameters only
* LoginStatus enum class was moved from site to login.py
* WbRepresentation derives from abstract base class abc.ABC
* Update characters in the Cf category to Unicode version 12.1.0
* Update __all__ variable in pywikibot (T122879)
* Use api.APIGenerator through site._generator (T129013)
* Support of MediaWiki releases below 1.19 has been dropped (T245350)
* Page.get_best_claim () retrieves preferred Claim of a property referring to the given page (T175207)
* Check whether _putthead is current_thread() to join() (T263331)
* Add BasePage.has_deleted_revisions() method
* Allow querying deleted revs without the deletedhistory right
* Use ignore_discard for login cookie container (T261066)
* Siteinfo.get() loads data via API instead from cache if expiry parameter is True (T260490)
* Move latest revision id handling to WikibaseEntity (T233406)
* Load wikibase entities when necessary (T245809)
* Fix path for stable release in version.getversion() (T262558)
* "since" parameter in EventStreams given as Timestamp or MediaWiki timestamp string has been fixed
* Methods deprecated for 6 years or longer were removed
* Page.getVersionHistory and Page.fullVersionHistory() methods were removed (T136513, T151110)
* Allow multiple types of contributors parameter given for Page.revision_count()
* Deprecated tools.UnicodeMixin and tools.IteratorNextMixin has been removed
* Localisation updates


4.3.0
-----

*2 September 2020*

* Don't check for valid Family/Site if running generate_user_files.py (T261771)
* Remove socket_timeout fix in config2.py introduced with T103069
* Prevent huge traceback from underlying python libraries (T253236)
* Localisation updates


4.2.0
-----

*28 August 2020*

* Add support for ja.wikivoyage (T261450)
* Only run cosmetic changes on wikitext pages (T260489)
* Leave a script gracefully for wrong -lang and -family option (T259756)
* Change meaning of BasePage.text (T260472)
* site/family methods code2encodings() and code2encoding() has been removed in favour of encoding()/endcodings() methods
* Site.getExpandedString() method was removed in favour of expand_text
* Site.Family() function was removed in favour of Family.load() method
* Add wikispore family (T260049)


4.1.1
-----

*18 August 2020*

* Add support for lldwiki to Pywikibot
* Fix getversion_git subprocess command


4.1.0
-----

*16 August 2020*

* Enable Pywikibot for Python 3.9
* APISite.loadpageinfo does not discard changes to page content when information was not loaded (T260472)
* tools.UnicodeType and tools.signature are deprecated
* BaseBot.stop() method is deprecated in favour of BaseBot.generator.close()
* Escape bot password correctly (T259488)
* Bugfixes and improvements
* Localisation updates


4.0.0
-----

*4 August 2020*

* Read correct object in SiteLinkCollection.normalizeData (T259426)
* tools.count and tools classes Counter, OrderedDict and ContextManagerWrapper were removed
* Deprecate UnicodeMixin and IteratorNextMixin
* Restrict site module interface
* EventStreams "since" parameter settings has been fixed
* Unsupported debug and uploadByUrl parameters of UploadRobot were removed
* Unported compat decode parameter of Page.title() has been removed
* Wikihow family file was added (T249814)
* Improve performance of CosmeticChangesToolkit.translateMagicWords
* Prohibit positional arguments with Page.title()
* Functions dealing with stars list were removed
* Some pagegenerators functions were deprecated which should be replaced by site generators
* LogEntry became a UserDict; all content can be accessed by its key
* URLs for new toolforge.org domain were updated
* pywikibot.__release__ was deprecated
* Use one central point for framework version (T106121, T171886, T197936, T253719)
* rvtoken parameter of Site.loadrevisions() and Page.revisions() has been dropped (T74763)
* getFilesFromAnHash and getImagesFromAnHash Site methods have been removed
* Site and Page methods deprecated for 10 years or longer have been removed
* Support for Python 2 and 3.4 has been dropped (T213287, T239542)
* Bugfixes and improvements
* Localisation updates

.. _python2:

3.0.20200703
------------

* Page.botMayEdit() method was improved (T253709)
* PageNotFound, SpamfilterError, UserActionRefuse exceptions were removed (T253681)
* tools.ip submodule has been removed (T243171)
* Wait in BaseBot.exit() until asynchronous saving pages are completed
* Solve IndexError when showing an empty diff with a non-zero context (T252724)
* linktrails were added or updated for a lot of sites
* Resolve namespaces with underlines (T252940)
* Fix getversion_svn for Python 3.6+ (T253617, T132292)
* Bugfixes and improvements
* Localisation updates


3.0.20200609
------------

* Fix page_can_be_edited for MediaWiki < 1.23 (T254623)
* Show global options with pwb.py -help
* Usage of SkipPageError with BaseBot has been removed
* Throttle requests after ratelimits exceeded (T253180)
* Make Pywikibot daemon logs unexecutable (T253472)
* Check for missing generator after BaseBot.setup() call
* Do not change usernames when creating a Site (T253127)
* pagegenerators: handle protocols in -weblink (T251308, T251310)
* Bugfixes and improvements
* Localisation updates


3.0.20200508
------------

* Unify and extend formats for setting sitelinks (T225863, T251512)
* Do not return a random i18n.translation() result (T220099)
* tools.ip_regexp has been removed (T174482)
* Page.getVersionHistory and Page.fullVersionHistory() methods has been desupported (T136513, T151110)
* Update wikimediachapter_family (T250802)
* Raise SpamblacklistError with spamblacklist APIError (T249436)
* SpamfilterError was renamed to SpamblacklistError (T249436)
* Do not removeUselessSpaces inside source/syntaxhighlight tags (T250469)
* Restrict Pillow to 6.2.2+ (T249911)
* Fix PetScan generator language and project (T249704)
* test_family has been removed (T228375, T228300)
* Bugfixes and improvements
* Localisation updates

3.0.20200405
------------

* Fix regression of combining sys.path in pwb.py wrapper (T249427)
* Site and Page methods deprecated for 10 years or longer are desupported and may be removed (T106121)
* Usage of SkipPageError with BaseBot is desupported and may be removed
* Ignore InvalidTitle in textlib.replace_links() (T122091)
* Raise ServerError also if connection to PetScan timeouts
* pagegenerators.py no longer supports 'oursql' or 'MySQLdb'. It now solely supports PyMySQL (T243154, T89976)
* Disfunctional Family.versionnumber() method was removed
* Refactor login functionality (T137805, T224712, T248767, T248768, T248945)
* Bugfixes and improvements
* Localisation updates

3.0.20200326
------------
* site.py and page.py files were moved to their own folders and will be split in the future
* Refactor data attributes of Wikibase entities (T233406)
* Functions dealing with stars list are desupported and may be removed
* Use path's stem of script filename within pwb.py wrapper (T248372)
* Disfunctional cgi_interface.py was removed (T248292, T248250, T193978)
* Fix logout on MW < 1.24 (T214009)
* Fixed TypeError in getFileVersionHistoryTable method (T248266)
* Outdated secure connection overrides were removed (T247668)
* Check for all modules which are needed by a script within pwb.py wrapper
* Check for all modules which are mandatory within pwb.py wrapper script
* Enable -help option with similar search of pwb.py (T241217)
* compat module has been removed (T183085)
* Category.copyTo and Category.copyAndKeep methods have been removed
* Site.page_restrictions() does no longer raise NoPage (T214286)
* Use site.userinfo getter instead of site._userinfo within api (T243794)
* Fix endprefix parameter in Category.articles() (T247201)
* Fix search for changed claims when saving entity (T246359)
* backports.py has been removed (T244664)
* Site.has_api method has been removed (T106121)
* Bugfixes and improvements
* Localisation updates

3.0.20200306
------------

* Fix mul Wikisource aliases (T242537, T241413)
* Let Site('test', 'test) be equal to Site('test', 'wikipedia') (T228839)
* Support of MediaWiki releases below 1.19 will be dropped (T245350)
* Provide mediawiki_messages for foreign language codes
* Use mw API IP/anon user detection (T245318)
* Correctly choose primary coordinates in BasePage.coordinates() (T244963)
* Rewrite APISite.page_can_be_edited (T244604)
* compat module is deprecated for 5 years and will be removed in next release (T183085)
* ipaddress module is required for Python 2 (T243171)
* tools.ip will be dropped in favour of tools.is_IP (T243171)
* tools.ip_regexp is deprecatd for 5 years and will be removed in next release
* backports.py will be removed in next release (T244664)
* stdnum package is required for ISBN scripts and cosmetic_changes (T132919, T144288, T241141)
* preload urllib.quote() with Python 2 (T243710, T222623)
* Drop isbn_hyphenate package due to outdated data (T243157)
* Fix UnboundLocalError in ProofreadPage._ocr_callback (T243644)
* Deprecate/remove sysop parameter in several methods and functions
* Refactor Wikibase entity namespace handling (T160395)
* Site.has_api method will be removed in next release
* Category.copyTo and Category.copyAndKeep will be removed in next release
* weblib module has been removed (T85001)
* botirc module has been removed (T212632)
* Bugfixes and improvements
* Localisation updates

3.0.20200111
------------

* Fix broken get_version() in setup.py (T198374)
* Rewrite site.log_page/site.unlock_page implementation
* Require requests 2.20.1 (T241934)
* Make bot.suggest_help a function
* Fix gui settings for Python 3.7.4+ (T241216)
* Better api error message handling (T235500)
* Ensure that required props exists as Page attribute (T237497)
* Refactor data loading for WikibaseEntities (T233406)
* replaceCategoryInPlace: Allow LRM and RLM at the end of the old_cat title (T240084)
* Support for Python 3.4 will be dropped (T239542)
* Derive LoginStatus from IntEnum (T213287, T239533)
* enum34 package is mandatory for Python 2.7 (T213287)
* call LoginManager with keyword arguments (T237501)
* Enable Pywikibot for Python 3.8 (T238637)
* Derive BaseLink from tools.UnicodeMixin (T223894)
* Make _flush aware of _putthread ongoing tasks (T147178)
* Add family file for foundation wiki (T237888)
* Fix generate_family_file.py for private wikis (T235768)
* Add rank parameter to Claim initializer
* Add current directory for similar script search (T217195)
* Release BaseSite.lock_page mutex during sleep
* Implement deletedrevisions api call (T75370)
* assert_valid_iter_params may raise AssertionError instead of pywikibot.Error (T233582)
* Upcast getRedirectTarget result and return the appropriate page subclass (T233392)
* Add ListGenerator for API:filearchive to site module (T230196)
* Deprecate the ability to login with a secondary sysop account (T71283)
* Enable global args with pwb.py wrapper script (T216825)
* Add a new ConfigParserBot class to set options from the scripts.ini file (T223778)
* Check a user's rights rather than group memberships; 'sysopnames' will be deprecated (T229293, T189126, T122705, T119335, T75545)
* proofreadpage.py: fix footer detection (T230301)
* Add allowusertalk to the User.block() options (T229288)
* botirc module will be removed in next release (T212632)
* weblib module will be removed in next release (T85001)
* Bugfixes and improvements
* Localisation updates

3.0.20190722
------------

* Increase the throttling delay if maxlag >> retry-after (T210606)
* deprecate test_family: Site('test', 'test'), use wikipedia_family: Site('test', 'wikipedia') instead (T228375, T228300)
* Add "user_agent_description" option in config.py
* APISite.fromDBName works for all known dbnames (T225590, 225723, 226960)
* remove the unimplemented "proxy" variable in config.py
* Make Family.langs property more robust (T226934)
* Remove strategy family
* Handle closed_wikis as read-only (T74674)
* TokenWallet: login automatically
* Add closed_wikis to Family.langs property (T225413)
* Redirect 'mo' site code to 'ro' and remove interwiki_replacement_overrides (T225417, T89451)
* Add support for badges on Wikibase item sitelinks through a SiteLink object instead plain str (T128202)
* Remove login.showCaptchaWindow() method
* New parameter supplied in suggest_help function for missing dependencies
* Remove NonMWAPISite class
* Introduce Claim.copy and prevent adding already saved claims (T220131)
* Fix create_short_link method after MediaWiki changes (T223865)
* Validate proofreadpage.IndexPage contents before saving it
* Refactor Link and introduce BaseLink (T66457)
* Count skipped pages in BaseBot class
* 'actionthrottledtext' is a retryable wikibase error (T192912)
* Clear tokens on logout(T222508)
* Deprecation warning: support for Python 2 will be dropped (T213287)
* botirc.IRCBot has been dropped
* Avoid using outdated browseragents (T222959)
* textlib: avoid infinite execution of regex (T222671)
* Add CSRF token in sitelogout() api call (T222508)
* Refactor WikibasePage.get and overriding methods and improve documentation
* Improve title patterns of WikibasePage extensions
* Add support for property creation (T160402)
* Bugfixes and improvements
* Localisation updates

3.0.20190430
------------

* Unicode literals are required for all scripts; the usage of ASCII bytes may fail (T219095)
* Don't fail if the number of forms of a plural string is less than required (T99057, T219097)
* Implement create_short_link Page method to use Extension:UrlShortener (T220876)
* Remove wikia family file (T220921)
* Remove deprecated ez_setup.py
* Changed requirements for sseclient (T219024)
* Set optional parameter namespace to None in site.logpages (T217664)
* Add ability to display similar scripts when misspelled (T217195)
* Check if QueryGenerator supports namespaces (T198452)
* Bugfixes and improvements
* Localisation updates

3.0.20190301
------------
* Fix version comparison (T164163)
* Remove pre MediaWiki 1.14 code
* Dropped support for Python 2.7.2 and 2.7.3 (T191192)
* Fix header regex beginning with a comment (T209712)
* Implement Claim.__eq__ (T76615)
* cleanup config2.py
* Add missing Wikibase API write actions
* Bugfixes and improvements
* Localisation updates

3.0.20190204
------------

* Support python version 3.7
* pagegenerators.py: add -querypage parameter to yield pages provided by any special page (T214234)
* Fix comparison of str, bytes and int literal
* site.py: add generic self.querypage() to query SpecialPages
* echo.Notification has a new event_id property as integer
* Bugfixes and improvements
* Localisation updates

3.0.20190106
------------

* Ensure "modules" parameter of ParamInfo._fetch is a set (T122763)
* Support adding new claims with qualifiers and/or references (T112577, T170432)
* Support LZMA and XZ compression formats
* Update correct-ar Typo corrections in fixes.py (T211492)
* Enable MediaWiki timestamp with EventStreams (T212133)
* Convert Timestamp.fromtimestampformat() if year, month and day are given only
* tools.concat_options is deprecated
* Additional ListOption subclasses ShowingListOption, MultipleChoiceList, ShowingMultipleChoiceList
* Bugfixes and improvements
* Localisation updates

3.0.20181203
------------

* Remove compat module references from autogenerated docs (T183085)
* site.preloadpages: split pagelist in most max_ids elements (T209111)
* Disable empty sections in cosmetic_changes for user namespace
* Prevent touch from re-creating pages (T193833)
* New Page.title() parameter without_brackets; also used by titletranslate (T200399)
* Security: require requests version 2.20.0 or later (T208296)
* Check appropriate key in Site.messages (T163661)
* Make sure the cookie file is created with the right permissions (T206387)
* pydot >= 1.2 is required for interwiki_graph
* Move methods for simple claim adding/removing to WikibasePage (T113131)
* Enable start timestamp for EventStreams (T205121)
* Re-enable notifications (T205184)
* Use FutureWarning for warnings intended for end users (T191192)
* Provide new -wanted... page generators (T56557, T150222)
* api.QueryGenerator: Handle slots during initialization (T200955, T205210)
* Bugfixes and improvements
* Localisation updates

3.0.20180922
------------

* Enable multiple streams for EventStreams (T205114)
* Fix Wikibase aliases handling (T194512)
* Remove cryptography support from python<=2.7.6 requirements (T203435)
* textlib._tag_pattern: Do not mistake self-closing tags with start tag (T203568)
* page.Link.langlinkUnsafe: Always set _namespace to a Namespace object (T203491)
* Enable Namespace.content for mw < 1.16
* Allow terminating the bot generator by BaseBot.stop() method (T198801)
* Allow bot parameter in set_redirect_target
* Do not show empty error messages (T203462)
* Show the exception message in async mode (T203448)
* Fix the extended user-config extraction regex (T145371)
* Solve UnicodeDecodeError in site.getredirtarget (T126192)
* Introduce a new APISite property: mw_version
* Improve hash method for BasePage and Link
* Avoid applying two uniquifying filters (T199615)
* Fix skipping of language links in CosmeticChangesToolkit.removeEmptySections (T202629)
* New mediawiki projects were provided
* Bugfixes and improvements
* Localisation updates

3.0.20180823
------------

* Don't reset Bot._site to None if we have already a site object (T125046)
* pywikibot.site.Siteinfo: Fix the bug in cache_time when loading a CachedRequest (T202227)
* pagegenerators._handle_recentchanges: Do not request for reversed results (T199199)
* Use a key for filter_unique where appropriate (T199615)
* pywikibot.tools: Add exceptions for first_upper (T200357)
* Fix usages of site.namespaces.NAMESPACE_NAME (T201969)
* pywikibot/textlib.py: Fix header regex to allow comments
* Use 'rvslots' when fetching revisions on MW 1.32+ (T200955)
* Drop the '2' from PYWIKIBOT2_DIR, PYWIKIBOT2_DIR_PWB, and PYWIKIBOT2_NO_USER_CONFIG environment variables. The old names are now deprecated. The other PYWIKIBOT2_* variables which were used only for testing purposes have been renamed without deprecation. (T184674)
* Introduce a timestamp in deprecated decorator (T106121)
* textlib.extract_sections: Remove footer from the last section (T199751)
* Don't let WikidataBot crash on save related errors (T199642)
* Allow different projects to have different L10N entries (T198889)
* remove color highlights before fill function (T196874)
* Fix Portuguese file namespace translation in cc (T57242)
* textlib._create_default_regexes: Avoid using inline flags (T195538)
* Not everything after a language link is footer (T199539)
* code cleanups
* New mediawiki projects were provided
* Bugfixes and improvements
* Localisation updates

3.0.20180710
------------

* Enable any LogEntry subclass for each logevent type (T199013)
* Deprecated pagegenerators options -<logtype>log aren't supported any longer (T199013)
* Open RotatingFileHandler with utf-8 encoding (T188231)
* Fix occasional failure of TestLogentries due to hidden namespace (T197506)
* Remove multiple empty sections at once in cosmetic_changes (T196324)
* Fix stub template position by putting it above interwiki comment (T57034)
* Fix handling of API continuation in PropertyGenerator (T196876)
* Use PyMySql as pure-Python MySQL client library instead of oursql, deprecate MySQLdb (T89976, T142021)
* Ensure that BaseBot.treat is always processing a Page object (T196562, T196813)
* Update global bot settings
* New mediawiki projects were provided
* Bugfixes and improvements
* Localisation updates

3.0.20180603
------------

* Move main categories to top in cosmetic_changes
* shell.py always imports pywikibot as default
* New roundrobin_generators in tools
* New BaseBot method "skip_page" to adjust page counting
* Family class is made a singleton class
* New rule 'startcolon' was introduced in textlib
* BaseBot has new methods setup and teardown
* UploadBot got a filename prefix parameter (T170123)
* cosmetic_changes is able to remove empty sections (T140570)
* Pywikibot is following PEP 396 versioning
* pagegenerators AllpagesPageGenerator, CombinedPageGenerator, UnconnectedPageGenerator are deprecated
* Some DayPageGenerator parameters has been renamed
* unicodedata2, httpbin and Flask dependency was removed (T102461, T108068, T178864, T193383)
* New projects were provided
* Bugfixes and improvements
* Documentation updates
* Localisation updates (T194893)
* Translation updates

3.0.20180505
------------

* Enable makepath and datafilepath not to create the directory
* Use API's retry-after value (T144023)
* Provide startprefix parameter for Category.articles() (T74101, T143120)
* Page.put_async() is marked as deprecated (T193494)
* pagegenerators.RepeatingGenerator is marked as deprecated (T192229)
* Deprecate requests-requirements.txt (T193476)
* Bugfixes and improvements
* New mediawiki projects were provided
* Localisation updates

3.0.20180403
------------

* Deprecation warning: support for Python 2.7.2 and 2.7.3 will be dropped (T191192)
* Dropped support for Python 2.6 (T154771)
* Dropped support for Python 3.3 (T184508)
* Bugfixes and improvements
* Localisation updates

3.0.20180304
------------

* Bugfixes and improvements
* Localisation updates

3.0.20180302
------------

* Changed requirements for requests and sseclient
* Bugfixes and improvements
* Localisation updates

3.0.20180204
------------

* Deprecation warning: support for py2.6 and py3.3 will be dropped
* Changed requirements for cryprography, Pillow and pyOpenSSL
* Bugfixes and improvements
* Localisation updates

3.0.20180108
------------

* Maintenance script to download Wikimedia database dump
* Option to auto-create accounts when logging in
* Ship wikimania family file
* Drop battlestarwiki family file
* Bugfixes and improvements
* Localisation updates

3.0.20171212
------------

* Introduce userscripts directory
* Generator settings inside (user-)fixes.py
* BaseUnlinkBot has become part of the framework in specialbots.py
* Decommission of rcstream
* Script files added to https://doc.wikimedia.org/pywikibot/
* Other documentation updates
* Bugfixes and improvements
* Localisation updates

3.0.20170801
------------

* Bugfixes and improvements
* Localisation updates

3.0.20170713
------------

* Deprecate APISite.newfiles()
* Inverse of pagegenerators -namespace option
* Bugfixes and improvements
* Localisation updates
* CODE_OF_CONDUCT included

Bugfixes
~~~~~~~~
* Manage temporary readonly error (T154011)
* Unbreak wbGeoShape and WbTabularData (T166362)
* Clean up issue with _WbDataPage (T166362)
* Re-enable xml for WikiStats with py2 (T165830)
* Solve httplib.IncompleteRead exception in eventstreams (T168535)
* Only force input_choise if self.always is given (T161483)
* Add colon when replacing category and file weblink (T127745)
* API Request: set uiprop only when ensuring 'userinfo' in meta (T169202)
* Fix TestLazyLoginNotExistUsername test for Stewardwiki (T169458)

Improvements
~~~~~~~~~~~~
* Introduce the new WbUnknown data type for Wikibase (T165961)
* djvu.py: add replace_page() and delete_page()
* Build GeoShape and TabularData from shared base class
* Remove non-breaking spaces when tidying up a link (T130818)
* Replace private mylang variables with mycode in generate_user_files.py
* FilePage: remove deprecated use of fileUrl
* Make socket_timeout recalculation reusable (T166539)
* FilePage.download(): add revision parameter to download arbitrary revision (T166939)
* Make pywikibot.Error more precise (T166982)
* Implement pywikibot support for adding thanks to normal revisions (T135409)
* Implement server side event client EventStreams (T158943)
* new pagegenerators filter option -titleregexnot
* Add exception for -namepace option (T167580)
* InteractiveReplace: Allow no replacements by default
* Encode default globe in family file
* Add on to pywikibot support for thanking normal revisions (T135409)
* Add log entry code for thanks log (T135413)
* Create superclass for log entries with user targets
* Use relative reference to class attribute
* Allow pywikibot to authenticate against a private wiki (T153903)
* Make WbRepresentations hashable (T167827)

Updates
~~~~~~~
* Update linktails
* Update languages_by_size
* Update cross_allowed (global bot wikis group)
* Add atjwiki to wikipedia family file (T168049)
* remove closed sites from languages_by_size list
* Update category_redirect_templates for wikipedia and commons Family
* Update logevent type parameter list
* Disable cleanUpSectionHeaders on jbo.wiktionary (T168399)
* Add kbpwiki to wikipedia family file (T169216)
* Remove anarchopedia family out of the framework (T167534)

3.0.20170521
------------

* Support for Python 2.6 but higher releases are strictly recommended
* Bugfixes and improvements
* Localisation updates

Bugfixes
~~~~~~~~
* Increase the default socket_timeout to 75 seconds (T163635)
* use repr() of exceptions to prevent UnicodeDecodeErrors (T120222)
* Handle offset mismatches during chunked upload (T156402)
* Correct _wbtypes equality comparison (T160282)
* Re-enable getFileVersionHistoryTable() method (T162528)
* Replaced the word 'async' with 'asynchronous' due to py3.7 (T106230)
* Raise ImportError if no editor is available (T163632)
* templatesWithParams: cache and standardise params (T113892)
* getInternetArchiveURL: Retry http.fetch if there is a ConnectionError (T164208)
* Remove wikidataquery from pywikibot (T162585)

Improvements
~~~~~~~~~~~~
* Introduce user_add_claim and allow asynchronous ItemPage.addClaim (T87493)
* Enable private edit summary in specialbots (T162527)
* Make a decorator for asynchronous methods
* Provide options by a separate handler class
* Show a warning when a LogEntry type is not known (T135505)
* Add Wikibase Client extension requirement to APISite.unconnectedpages()
* Update content after editing entity
* Make WbTime from Timestamp and vice versa (T131624)
* Add support for geo-shape Wikibase data type (T161726)
* Add async parameter to ItemPage.editEntity (T86074)
* Make sparql use Site to access sparql endpoint and entity_url (T159956)
* timestripper: search wikilinks to reduce false matches
* Set Coordinate globe via item
* use extract_templates_and_params_regex_simple for template validation
* Add _items for WbMonolingualText
* Allow date-versioned pypi releases from setup.py (T152907)
* Provide site to WbTime via WbTime.fromWikibase
* Provide preloading via GeneratorFactory.getCombinedGenerator() (T135331)
* Accept QuitKeyboardInterrupt in specialbots.Uploadbot (T163970)
* Remove unnecessary description change message when uploading a file (T163108)
* Add 'OptionHandler' to bot.__all__ tuple
* Use FilePage.upload inside UploadRobot
* Add support for tabular-data Wikibase data type (T163981)
* Get thumburl information in FilePage() (T137011)

Updates
~~~~~~~
* Update languages_by_size in family files
* wikisource_family.py: Add "pa" to languages_by_size
* Config2: limit the number of retries to 15 (T165898)

3.0.20170403
------------

* First major release from master branch
* requests package is mandatory
* Deprecate previous 2.0 branches and tags

Bugfixes
~~~~~~~~
* Use default summary when summary value does not contain a string (T160823)
* Enable specialbots.py for PY3 (T161457)
* Change tw(n)translate from Site.code to Site.lang dependency (T140624)
* Do not use the "imp" module in Python 3 (T158640)
* Make sure the order of parameters does not change (T161291)
* Use pywikibot.tools.Counter instead of collections.Counter (T160620)
* Introduce a new site method page_from_repository()
* Add pagelist tag for replaceExcept (T151940)
* logging in python3 when deprecated_args decorator is used (T159077)
* Avoid ResourceWarning using subprocess in python 3.6 (T159646)
* load_pages_from_pageids: do not fail on empty string (T153592)
* Add missing not-equal comparison for wbtypes (T158848)
* textlib.getCategoryLinks catch invalid category title exceptions (T154309)
* Fix html2unicode (T130925)
* Ignore first letter case on 'first-letter' sites, obey it otherwise (T130917)
* textlib.py: Limit catastrophic backtracking in FILE_LINK_REGEX (T148959)
* FilePage.get_file_history(): Check for len(self._file_revisions) (T155740)
* Fix for positional_arg behavior of GeneratorFactory (T155227)
* Fix broken LDAP based login (T90149)

Improvements
~~~~~~~~~~~~
* Simplify User class
* Renamed isImage and isCategory
* Add -property option to pagegenerators.py
* Add a new site method pages_with_property
* Allow retrieval of unit as ItemPage for WbQuantity (T143594)
* return result of userPut with put_current method
* Provide a new generator which yields a subclass of Page
* Implement FilePage.download()
* make general function to compute file sha
* Support adding units to WbQuantity through ItemPage or entity url (T143594)
* Make PropertyPage.get() return a dictionary
* Add Wikibase Client extension requirement to APISite.unconnectedpages()
* Make Wikibase Property provide labels data
* APISite.data_repository(): handle warning with re.match() (T156596)
* GeneratorFactory: make getCategory respect self.site (T155687)
* Fix and improve default regexes

Updates
~~~~~~~
* Update linktrails
* Update languages_by_size
* Updating global bot wikis, closed wikis and deleted wikis
* Deprecate site.has_transcluded_data
* update plural rules
* Correcting month names in date.py for Euskara (eu)
* Linktrail for Euskara
* Define template documentation subpages for es.wikibooks
* self.doc_subpages for Meta-Wiki
* Updating Wikibooks projects which allows global bots
* Updated list of closed projects
* Add 'Bilde' as a namespace alias for file namespace of nn Wikipedia (T154947)

2.0rc5
------

*17 August 2016*

* Last stable 2.0 branch

Bugfixes
~~~~~~~~
* Establish the project's name, once and for all
* setup.py: Add Python 3.4 and 3.5 to pypi classifiers
* Remove item count output in page generators
* Test Python 3.5 on Travis
* Fix docstring capitalization in return types and behavior
* Stop reading 'cookieprefix' upon login
* Fix travis global environment variables
* Fix notifications building from JSON
* pywikibot: Store ImportError in imported variable
* Use default tox pip install
* Add asteroids that are being used as locations
* [bugfix] Fix test_translateMagicWords test
* Fix ID for Rhea
* [bugfix] pass User page object to NotEmailableError
* Allow pywikibot to run on Windows 10 as well
* listpages.py: Fix help docstring
* pwb.py: make sure pywikibot is correctly loaded before starting a script
* win32_unicode: force truetype font in console
* Update main copyright year to 2016
* [L10N] add "sco" to redirected category pages
* date.py: fix Hungarian day-month title
* Prevent <references.../> from being destroyed
* [FIX] Page: Use repr-like if it can't be encoded
* pywikibot.WARNING -> pywikibot.logging.WARNING
* Do not expand text by default in getCategoryLinks
* Typo fix
* Prevent AttributeError for when filename is None
* Split TestUserContribs between user and non-user

2.0rc4
------

*15 December 2015*

Bugfixes
~~~~~~~~
* Remove dependency on pYsearch
* Require google>=0.7
* Desupport Python 2.6 for Pywikibot 2.0 release branch
* config: Don't crash on later get_base_dir calls
* cosmetic_changes: merge similar regexes
* Update revId upon claim change
* Update WOW hostnames
* Mark site.patrol() as a user write action
* Fix interwikiFormat support for Link
* Changes are wrongly detected in the last langlink
* getLanguageLinks: Skip own site
* fix intersection of sets of namespaces
* Import textlib.TimeStripper
* Change "PyWikiBot" to "Pywikibot"
* Stop crashing item loads due to support of units
* __all__ items must be bytes on Python 2
* Omit includeredirects parameter for allpages generator
* Performance fix for sites using interwiki_putfirst option
* Fix Persian Wikipedia configuration
* rollback: Use Revision instance properly
* Add must_be to DataSite write actions
* Remove unneeded site argument to AutoFamily
* Fix ComparableMixin
* Deprecate ParamInfo.query_modules_with_limits
* be-x-old is renamed to be-tarask
* Correctly identify qualifier from JSON

2.0rc3
------

*30 September 2015*

Bugfixes
~~~~~~~~
* New Wikipedia site: azb
* Indexes in str.format
* MediaWikiVersion: Accept new wmf style
* i18n: always follow master
* Bugfixes
* Localisation updates
* i18n: always follow master branch
* exception.UploadWarning was replaced by data.api.UploadWarning

2.0rc2
------

*9 July 2015*

Configuration updates
~~~~~~~~~~~~~~~~~~~~~
* Changing the sandbox content template on Fa WP

Family file updates
~~~~~~~~~~~~~~~~~~~
* Remove broken wikis from battlestarwiki family
* Adding euskara and sicilianu languages to Vikidia family
* WOW Wiki subdomains hr, ro & sr deleted
* Add new Wikipedia languages gom and lrc

Bugfixes
~~~~~~~~
* fix UnicodeDecodeError on api error
* pwb.py now correctly passes arguments to generate_family_file
* Fix Win32 config.editor detection
* open_compressed: Wrap BZ2File in Py 2.7
* Skip RC entries without a title
* PatrolEntry: Allow cur/prev id to be str
* Updates to i18n changes
* Do not use ParamInfo during action=login
* Let pydot encode labels for Python 3 support
* Fix and test interwiki_graph
* textlib: replaceExcept: Handle empty matches
* Bugfixes and improvements
* Localisation updates


2.0rc1
------

*25 May 2015*

Major improvements include:

* Sphinx documentation at https://doc.wikimedia.org/pywikibot/
* Initial ProofreadPage support
* Improved diff output, with context
* Batch upload support
* Compat scripts patrol.py and piper.py ported
* isbn.py now supports wikibase
* RecentChanges stream (rcstream) support

Pywikibot API improvements include:

* Python 3 ipaddress support
* Support for Python warning system
* Wikibase:
   - added ISBN support
   - added redirect support
* Optionally uses external library for improved isbn validation
* Automatically generating user files when -user, -family and -lang are
  provided to a script
* Page.content_model added
* Page.contributors() and Page.revision_count() added
* APISite.compare added
* Site.undelete and Page.undelete added
* DataSite.search_entities support
* FilePage.latest_file_info and FilePage.oldest_file_info added
* ItemClaimFilterPageGenerator added

Low-level changes include:

* Switch to JSON-based i18n data format
* Unicode_literals used throughout source code
* API badtoken recovery
* API client side prevention of anonymous writes
* API layer support for boolean and date datatypes
* Improved MediaWiki version detection
* PageNotFound exception is no longer used
* UserActionRefuse exception was replaced by UserRightsError and NotEmailableError

Other changes include:

* Python 3 support fixes
* Daemonize support
* Allow pywikibot to load without i18n data
* Appveyor CI Win32 builds
* New scripts patrol.py and piper.py ported from old compat branch
* Bugfixes and improvements
* Localisation updates

2.0b3
-----

*30 November 2014*

Major changes include:

* Library initialisation no longer connects to servers
* generate_user_files.py rewritten
* API Version 1.14 support
* Support HTTPS for families with certificate validation errors (Python 2 only)
* API HTTP(S) GET support
* API simplified continuation support
* Upload uses a fake filename to avoid various MIME encoding issues
* API class ParamInfo inspects API modules
* Several QueryGenerator efficiency improvements
* Improved 'same title' detection and 'get redirect target' handling
* Site interwiki methods now use dynamic Interwikimap
* Site methods return Namespace object instead of int
* New WikiStats module
* New PatchManager module used for showDiff
* New pagegenerators, including -intersect support
* Several category_redirect.py improvements
* archivebot: support more languages
* reflinks: changed from GPL to MIT
* Bugfixes and improvements

2.0b2
-----

*7 October 2014*

* Bugfixes and improvements

2.0b1
-----

*26 August 2013*

* First stable release branch

1.0 rv 2007-06-19
-----------------
* BeautifulSoup becomes mandatory
* new scripts were added
* new family files were supported
* some scripts were archived

1.0
---

*26 September 2005*

* First PyWikipediaBot framework release
* scripts and libraries for standardizing content
* tools for making minor modifications
* script making interwiki links
