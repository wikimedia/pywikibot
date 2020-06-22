Release history
===============

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
* Add support for badges on Wikibase item sitelinks (T128202)
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

*Sep 26, 2005*

* First PyWikipediaBot framework release
* scripts and libraries for standardizing content
* tools for making minor modifications
* script making interwiki links
