Release history
===============

8.1.1
-----
*21 April 2023*

* Add support for fatwikipedia (:phab:`T335021`)
* Add support for kcgwiktionary (:phab:`T334742`)
* Update for wowwiki family


8.1.0
-----
*16 April 2023*

* :mod:`generate_family_file<pywikibot.scripts.generate_family_file>` script was improved (:phab:`T334775`)
* A ``quiet`` parameter was added to :meth:`APISite.preloadpages()
  <pywikibot.site._generators.GeneratorsMixin.preloadpages>` which is True by default
* Fix getting HTTPStatus enum in site_detect check_response (:phab:`T334728`)
* Do not show a logging in message if password is entered (:phab:`T178061`)
* Enable preleading ``Bot:`` prefix with twtranslate messages (:phab:`T161459`)
* Disable command.log if -nolog option is given (:phab:`T334381`)
* Guess the last needed token key if the token is not found (:phab:`T334288`)
* Show parameters with APIError (:phab:`T333957`)
* Raise :exc:`exceptions.NoSiteLinkError` instead of :exc:`exceptions.NoPageError` when sitelink
  is missing in :meth:`ItemPage.getSitelink()<pywikibot.ItemPage.getSitelink>` (:phab:`T332341`)
* :exc:`exceptions.ClientError` was added
* Raise :exc:`exceptions.NoPageError` when deleting a missing Page (:phab:`T332924`)
* ``text`` parameter of :class:`proofreadpage.PagesTagParser` has a default value
* L10N updates
* Ignore talk pages with :meth:`APISite.watched_pages()<pywikibot.site._generators.GeneratorsMixin.watched_pages>` (:phab:`T330806`)
* Load page info when creating a page if not updated previously (:phab:`T330980`)
* Improve flush exception logging


8.0.4
-----
*13 April 2023*

* L10N Updates
* Minimal needed mwparserfromhell was decreased to 0.5.2 (:phab:`T326498`, :phab:`T327600`)
* No longer lazy load password cookies (:phab:`T271858`, :phab:`T326779`, :phab:`T329132`, :phab:`T330488`, :phab:`T331315`)


8.0.3
-----
*29 March 2023*

* Add support for ckb-wiktionary (:phab:`T332093`)


8.0.2
-----
*25 March 2023*

* Add support for anpwiki (:phab:`T332115`)


8.0.1
-----
*04 March 2023*

* Add support for azwikimedia, gucwiki, gurwiki (:phab:`T317121`, :phab:`T326238`, :phab:`T327844`)
* Avoid error when replacement includes backslash (:phab:`T330021`)
* Copy snak IDs/hashes when using :meth:`page.WikibaseEntity.editEntity` (:phab:`T327607`)
* Add ``timezone_aware`` to :meth:`pywikibot.WbTime.toTimestamp` (:phab:`T325868`)
* L10N and i18n updates


8.0.0
-----
*21 January 2023*

Improvements
^^^^^^^^^^^^

* Allow copying timezone from timestamp in :class:`pywikibot.WbTime` (:phab:`T325864`)
* Support federated Wikibase (:phab:`T173195`)
* Improve warning if a Non-JSON response was received from server (:phab:`T326046`)
* Allow normalization of :class:`pywikibot.WbTime` objects (:phab:`T123888`)
* Add parser for ``<pages />`` tag to :mod:`proofreadpage`
* ``addOnly`` parameter of :func:`textlib.replaceLanguageLinks` and :func:`textlib.replaceCategoryLinks`
  were renamed to ``add_only``
* ``known_codes`` attribute was added to :class:`family.WikimediaFamily` (:phab:`T325426`)
* Unify representation for :class:`time.Timestamp` between  CPython and Pypy (:phab:`T325905`)
* Implement comparison for :class:`pywikibot.WbTime` object (:phab:`T148280`, :phab:`T325863`)
* Create a cookie file for each account (:phab:`T324000`)
* Move data.api._login.LoginManager to :class:`login.ClientLoginManager`
* Let user the choice which section to be copied with :mod:`generate_user_files
  <pywikibot.scripts.generate_user_files>` (:phab:`T145372`)
* use :func:`roundrobin_generators<tools.itertools.roundrobin_generators>` to combine generators
  when limit option is given
* Ignore OSError if API cache cannot be written
* Update tools._unidata._category_cf from Unicodedata version 15.0.0
* :meth:`Timestamp.set_timestamp()<pywikibot.time.Timestamp.set_timestamp>` raises TypeError
  instead of ValueError if conversion fails
* Python 3.12 is supported
* All parameters of :meth:`APISite.categorymembers()
  <pywikibot.site._generators.GeneratorsMixin.categorymembers>` are provided with
  :meth:`Category.members()<page.Category.members>`,
  :meth:`Category.subcategories()<page.Category.subcategories>` (*member_type* excluded) and
  :meth:`Category.articles()<page.Category.articles>` (*member_type* excluded)
* Enable site-package installation from git repository (:phab:`T320851`)
* Enable 2FA login (:phab:`T186274`)
* :meth:`Page.editTime()<page.BasePage.editTime>` was replaced by
  :attr:`Page.latest_revision.timestamp<page.BasePage.latest_revision>`
* Raise a generic ServerError if requests response is a ServerError (:phab:`T320590`)
* Add a new variable 'private_folder_permission' to config.py (:phab:`T315045`)
* L10N and i18n updates
* Adjust subprocess args in :mod:`tools.djvu`
* Short site value can be given if site code is equal to family like ``-site:meta`` or ``-site:commons``

Documentation improvements
^^^^^^^^^^^^^^^^^^^^^^^^^^

* Add highlighting to targeted code snippet within documentation (:phab:`T323800`)
* Add previous, next, index, and modules links to documentation sidebar (:phab:`T323803`)
* Introduce standard colors (legacy palette) in Furo theme (:phab:`T323802`)
* Improve basic content structure and navigation of documentation (:phab:`T323812`)
* Use ``Furo`` sphinx theme instead of ``Natural`` and improve documentation look and feel (:phab:`T322212`)
* MediaWiki API cross reference was added to the documentation

Bugfixes
^^^^^^^^

* Fix representation string for :class:`page.Claim` stub instances (:phab:`T326453`)
* Don't raise StopIteration in :meth:`login.LoginManager.check_user_exists`
  if given user is behind the last user (:phab:`T326063`)
* Normalize :class:`WbTimes<pywikibot.WbTime>` sent to Wikidata (:phab:`T325860`)
* Fix :class:`pywikibot.WbTime` precision (:phab:`T324798`)
* Unquote title for red-links in class:`proofreadpage.IndexPage`
* Find month with first letter uppercase or lowercase with :class:`textlib.TimeStripper` (:phab:`T324310`)
* Fix disolving script_paths for site-package (:phab:`T320530`)
* Respect limit argument with Board.topics() (:phab:`T138215`, :phab:`T138307`)

Breaking changes
^^^^^^^^^^^^^^^^

* ``mwparserfromhell`` package is mandatory (:phab:`T326498`)
* Several package dependencies were updated
* All parameters of :meth:`Category.members()<page.Category.members>`,
  :meth:`Category.subcategories()<page.Category.subcategories>` and
  :meth:`Category.articles()<page.Category.articles>` are keyword only
* The ``parent_id`` and ``content_model`` attributes of :class:`page.Revision` were removed in favour
  of ``parentid`` and ``contentmodel``
* Support for MediaWiki < 1.27 was dropped
* ListBoxWindows class of :mod:`userinterfaces.gui` was removed
* Require Python 3.6.1+ with Pywikibot and drop support for Python 3.6.0 (:phab:`T318912`)
* pymysql >= 0.9.3 is required (:phab:`T216741`)
* Python 3.5 support was dropped (:phab:`T301908`)
* *See also Code cleanups below*

Code cleanups
^^^^^^^^^^^^^

* ``maintenance/sorting_order`` script was removed (:phab:`T325426`)
* ``alphabetic_sv`` and ``interwiki_putfirst`` attributes of
  :class:`Wiktionary<families.wiktionary_family.Family>` family were removed (:phab:`T325426`)
* ``alphabetic``, ``alphabetic_revised`` and ``fyinterwiki`` attributes of :class:`family.Family`
  were removed (:phab:`T325426`)


7.7.3
-----
*08 January 2023*

* Add support for shn-wikibooks, as quote, guw quote, got-wikt families
  (:phab:`T148280`, :phab:`T326141`, :phab:`T321285`, :phab:`T321297`)

7.7.2
-----
*03 December 2022*

* Fix :class:`textlib.TimeStripper` for ``vi`` site code (:phab:`T324310`)

7.7.1
-----

*10 October 2022*

* New wikis are supported (:phab:`T314642`, :phab:`T314648`, :phab:`T316459`, :phab:`T317115`, :phab:`T319193`)


7.7.0
-----
*25 September 2022*

* TypeError is raised if *aliases* parameter of :meth:`WikibasePage.editAliases
  <page.WikibasePage.editEntity>` method is not a list (:phab:`T318034`)
* Raise TypeError in :meth:`AliasesDict.normalizeData
  <pywikibot.page._collections.AliasesDict.normalizeData>` if *data* value is not a list (:phab:`T318034`)
* tools' threading classes were moved to :mod:`tools.threading` submodule
* No longer raise NotimplementedError in :meth:`APISite.page_from_repository
  <pywikibot.site._apisite.APISite.page_from_repository>` (:phab:`T318033`)
* Ability to set ``PYWIKIBOT_TEST_...`` environment variables with pwb wrapper (:phab:`T139847`)
* OmegaWiki family was removed
* Provide global ``-config`` option to specify the user config file name
* Run :mod:`pywikibot.scripts.login` script in parallel tasks if ``-async`` option is given (:phab:`T57899`)
* Ability to preload categories was added to :meth:`APISite.preloadpages
  <pywikibot.site._generators.GeneratorsMixin.preloadpages>` (:phab:`T241689`)
* Add :class:`WikiBlame<page._toolforge.WikiBlameMixin>` support was added to get the five topmost authors
* Raise KeyError instead of AttributeError if :class:`page.FileInfo` is used as Mapping
* i18n and L10N updates


7.6.0
-----
*21 August 2022*

* Add support for pcmwiki, guvwikt and bjnwikt (:phab:`T309059`, :phab:`T310882`, :phab:`T312217`)
* support *not* loading text :meth:`site.APISite.preloadpages` (:phab:`T67163`)
* :func:`textlib.TimeStripper.timestripper` removes HTML elements before searching for
  timestamp in text (:phab:`T302496`)
* backport :mod:`backports.pairwise()<backports>` from Python 3.10
* L10N updates
* Fix partial caching in :meth:`Category.subcategories()<page.Category.subcategories>` (:phab:`T88217`)
* Method :meth:`Page.has_content()<page.BasePage.has_content>` was added (:phab:`T313736`)
* Discard cache and reload it if cache was loaded without content and content is required
  in :meth:`Page.templates()<page.BasePage.templates>` (:phab:`T313736`)
* Add support for vikidia:oc
* Exit loop in PageFromFileReader if match.end() <= 0 (:phab:`T313684`)
* Allow Exception as parameter of pywikibot.exceptions.Error
* Make :func:`GoogleSearchPageGenerator<pagegenerators.GoogleSearchPageGenerator>`
  and :func:`PetScanPageGenerator<pagegenerators.PetScanPageGenerator>` a restartable
  Generator (:phab:`T313681`, :phab:`T313683`)
* Provide a :class:`collections.GeneratorWrapper<tools.collections.GeneratorWrapper>`
  class to start/restart a generator (:phab:`T301318`, :phab:`T312654`, :phab:`T312883`)
* tools' itertools functions were moved to :mod:`tools.itertools` submodule
* tools' collections classes were moved to :mod:`tools.collections` submodule
* Set successful login status for the OAuth case (:phab:`T313571`)


7.5.0
-----
*22 July 2022*

* Add support for blkwiki (:phab:`T310875`)
* L10N Updates
* Fix duplicate source detection in :meth:`pywikibot.WikidataBot.user_add_claim_unless_exists`
* :mod:`pywikibot.textlib`.tzoneFixedOffset class was renamed to :class:`pywikibot.time.TZoneFixedOffset`
* Wrapper method :meth:`parsevalue()<pywikibot.site._datasite.DataSite.parsevalue>`
  around wbparsevalue was added (:phab:`T112140`, :phab:`T312755`)
* L10N updates
* Fix cp encodings in :func:`get_charset_from_content_type()
  <comms.http.get_charset_from_content_type>` (:phab:`T312230`)
* New :mod:`pywikibot.time` module with new functions in addition to `Timestamp`
* :meth:`Page.revisions()<page.BasePage.revisions>` supports more formats/types for
  starttime and endtime parameters, in addition to those allowed by
  :meth:`Timestamp.fromISOformat()<pywikibot.Timestamp.fromISOformat>`.
* New :meth:`Timestamp.set_timestamp()<pywikibot.Timestamp.set_timestamp>` method
* Fully ISO8601 and POSIX format support with :class:`pywikibot.Timestamp`;
  formats are compliant with MediaWiki supported formats
* Handle asynchronous page_put_queue after KeyboardInterrupt in Python 3.9+ (:phab:`T311076`)
* No longer expect a specific namespace alias in cosmetic_changes
  :meth:`translateAndCapitalizeNamespaces
  <cosmetic_changes.CosmeticChangesToolkit.translateAndCapitalizeNamespaces>`


7.4.0
-----
*26 June 2022*

* Provide Built Distribution with Pywikibot (:pep:`427`)
* Update `WRITE_ACTIONS` in used by :class:`api.Request<data.api.Request>`
* Move :func:`get_closest_memento_url<data.memento.get_closest_memento_url>` from weblinkchecker script to memento module.
* Add :mod:`memento module<data.memento>` to fix memento_client package (:phab:`T185561`)
* L10N and i18n updates
* Fix Flow board topic continuation when iterating in reverse (:phab:`T138323`)
* Add Avestan transliteration
* Use Response.json() instead of json.loads(Response.text)
* Show an APIError if PetScanPageGenerator.query() fails (:phab:`T309538`)
* `login.py` is now a utiliy script even for site-package installation (:phab:`T309290`)
* `preload_sites.py` is now a utiliy script even for site-package installation (:phab:`T308912`)
* :attr:`generator_completed<bot.BaseBot.generator_completed>` became a public attribute
* Return gracefully from pwb.find_alternates if folder in user_script_paths does not exist (:phab:`T308910`)


7.3.0
-----
*21 May 2022*

* Add support for kcgwiki (:phab:`T305282`)
* Raise InvalidTitleError instead of unspecific ValueError in ProofreadPage (:phab:`T308016`)
* Preload pages if GeneratorFactory.articlenotfilter_list is not empty; also set attribute ``is_preloading``.
* ClaimCollection.toJSON() should not ignore new claim (:phab:`T308245`)
* use linktrail via siteinfo and remove `update_linkrtrails` maintenance script
* Print counter statistic for all counters (:phab:`T307834`)
* Use proofreadpagesinindex query module
* Prioritize -namespaces options in `pagegenerators.handle_args` (:phab:`T222519`)
* Remove `ThreadList.stop_all()` method (:phab:`T307830`)
* L10N updates
* Improve get_charset_from_content_type function (:phab:`T307760`)
* A tiny cache wrapper was added to hold results of parameterless methods and properties
* Increase workers in preload_sites.py
* Close logging handlers before deleting them (:phab:`T91375`, :phab:`T286127`)
* Clear _sites cache if called with pwb wrapper (:phab:`T225594`)
* Enable short creation of a site if family name is equal to site code
* Use `exc_info=True` with pywikibot.exception() by default (:phab:`T306762`)
* Make IndexPage more robust when getting links in Page ns (:phab:`T307280`)
* Do not print log header twice in log files (:phab:`T264235`)
* Do not delegate logging output to the root logger (:phab:`T281643`)
* Add `get_charset_from_content_type` to extract the charset from the content-type response header


7.2.0
-----
*26 April 2022*

* Make logging system consistent, add pywikibot.info() alias for pywikibot.output() (:phab:`T85620`)
* L10N updates
* Circumvent circular import in tools module (:phab:`T306760`)
* Don't fix html inside syntaxhighlight parts in fixes.py (:phab:`T306723`)
* Make layer parameter optional in `pywikibot.debug()` (:phab:`T85620`)
* Retry for internal_api_error_DBQueryTimeoutError errors due to :phab:`T297708`
* Handle ParserError within xmlreader.XmlDump.parse() instead of raising an exception (:phab:`T306134`)
* XMLDumpOldPageGenerator is deprecated in favour of a `content` parameter (:phab:`T306134`)
* `use_disambig` BaseBot attribute was added to hande disambig skipping
* Deprecate RedirectPageBot and NoRedirectPageBot in favour of `use_redirects` attribute
* tools.formatter.color_format is deprecated and will be removed
* A new and easier color format was implemented; colors can be used like:
    ``'this is a <<green>>colored<<default>> text'``
* Unused and unsupported `xmlreader.XmlParserThread` was removed
* Use upercased IP user titles (:phab:`T306291`)
* Use pathlib to extract filename and file_package in pwb.py
* Fix isbn messages in fixes.py (:phab:`T306166`)
* Fix Page.revisions() with starttime (:phab:`T109181`)
* Use stream_output for messages inside input_list_choice method (:phab:`T305940`)
* Expand simulate query result (:phab:`T305918`)
* Do not delete text when updating a Revision (:phab:`T304786`)
* Re-enable scripts package version check with pwb wrapper (:phab:`T305799`)
* Provide textlib.ignore_case() as a public method
* Don't try to upcast timestamp from global userinfo if global account does not exists (:phab:`T305351`)
* Archived scripts were removed; create a Phabricator task to restore some (:phab:`T223826`)
* Add Lexeme support for Lexicographical data (:phab:`T189321`, :phab:`T305297`)
* enable all parameters of `APISite.imageusage()` with `FilePage.using_pages()`
* Don't raise `NoPageError` with `file_is_shared` (:phab:`T305182`)
* Fix URL of GoogleOCR
* Handle ratelimit with purgepages() (:phab:`T152597`)
* Add movesubpages parameter to Page.move() and APISite.movepage() (:phab:`T57084`)
* Do not iterate over sys.modules (:phab:`T304785`)


7.1.0
-----
*26 March 2022*

* Add FilePage.file_is_used property to determine whether a file is used on a site
* Add support for guwwiki and shnwikivoyage (:phab:`T303762`, :phab:`T302799`)
* TextExtracts support was aded (:phab:`T72682`)
* Unused `get_redirect` parameter of Page.getOldVersion() has been dropped
* Provide BasePage.get_parsed_page() as a public method
* Provide BuiltinNamespace.canonical_namespaces() with BuiltinNamespace IntEnum
* BuiltinNamespace got a canonical() method
* Enable nested templates with MultiTemplateMatchBuilder (:phab:`T110529`)
* Introduce APISite.simple_request as a public method
* Provide an Uploader class to upload files
* Enable use of deletetalk parameter of the delete API
* Fix contextlib redirection for terminal interfaces (:phab:`T283808`)
* No longer use win32_unicode for Python 3.6+ (:phab:`T281042`, :phab:`T283808`, :phab:`T303373`)
* L10N updates
* -cosmetic_changes (-cc) option allows to assign the value directly instead of toggle it
* distutils.util.strtobool() was implemented as tools.strtobool() due to :pep:`632`
* The "in" operator always return whether the siteinfo contains the key even it is not cached (:phab:`T302859`)
* Siteinfo.clear() and  Siteinfo.is_cached() methods were added


7.0.0
-----
*26 February 2022*

Improvements
^^^^^^^^^^^^

* i18n updates for date.py
* Add number transliteration of 'lo', 'ml', 'pa', 'te' to NON_LATIN_DIGITS
* Detect range blocks with Page.is_blocked() method (:phab:`T301282`)
* to_latin_digits() function was added to textlib as counterpart of to_local_digits() function
* api.Request.submit now handles search-title-disabled and search-text-disabled API Errors
* A show_diff parameter  was added to Page.put() and Page.change_category()
* Allow categories when saving IndexPage (:phab:`T299806`)
* Add a new function case_escape to textlib
* Support inheritance of the __STATICREDIRECT__
* Avoid non-deteministic behavior in removeDisableParts
* Update isbn dependency and require python-stdnum >= 1.17
* Synchronize Page.linkedPages() parameters with Site.pagelinks() parameters
* Scripts hash bang was changed from python to python3
* i18n.bundles(), i18n.known_languages and  i18n._get_bundle() functions were added
* Raise ConnectionError immediately if urllib3.NewConnectionError occurs (:phab:`T297994`, :phab:`T298859`)
* Make pywikibot messages available with site package (:phab:`T57109`, :phab:`T275981`)
* Add support for API:Redirects
* Enable shell script with Pywikibot site package
* Enable generate_user_files.py and generate_family_file with site-package (:phab:`T107629`)
* Add support for Python 3.11
* Pywikibot supports PyPy 3 (:phab:`T101592`)
* A new method User.is_locked() was added to determine whether the user is currently locked globally (:phab:`T249392`)
* A new method APISite.is_locked() was added to determine whether a given user or user id is locked globally (:phab:`T249392`)
* APISite.get_globaluserinfo() method was added to retrieve globaluserinfo for any user or user id (:phab:`T163629`)
* APISite.globaluserinfo attribute may be deleted to force reload
* APISite.is_blocked() method has a force parameter to reload that info
* Allow family files in base_dir by default
* Make pwb wrapper script a pywikibot entry point for scripts (:phab:`T139143`, :phab:`T270480`)
* Enable -version and --version with pwb wrapper or code entry point (:phab:`T101828`)
* Add `title_delimiter_and_aliases` attribute to family files to support WikiHow family (:phab:`T294761`)
* BaseBot has a public collections.Counter for reading, writing and skipping a page
* Upload: Retry upload if 'copyuploadbaddomain' API error occurs (:phab:`T294825`)
* Update invisible characters from unicodedata 14.0.0
* Add support for Wikimedia OCR engine with proofreadpage
* Rewrite :func:`tools.itertools.intersect_generators` which makes it running up to 10'000 times faster. (:phab:`T85623`, :phab:`T293276`)
* The cached output functionality from compat release was re-implemented (:phab:`T151727`, :phab:`T73646`, :phab:`T74942`, :phab:`T132135`, :phab:`T144698`, :phab:`T196039`, :phab:`T280466`)
* L10N updates
* Adjust groupsize within pagegenerators.PreloadingGenerator (:phab:`T291770`)
* New "maxlimit" property was added to APISite (:phab:`T291770`)

Bugfixes
^^^^^^^^

* Don't raise an exception if BlockEntry initializer found a hidden title (:phab:`T78152`)
* Fix KeyError in create_warnings_list (:phab:`T301610`)
* Enable similar script call of pwb.py on toolforge (:phab:`T298846`)
* Remove question mark character from forbidden file name characters (:phab:`T93482`)
* Enable -interwiki option with pagegenerators (:phab:`T57099`)
* Don't assert login result (:phab:`T298761`)
* Allow title placeholder $1 in the middle of an url (:phab:`T111513`, :phab:`T298078`)
* Don't create a Site object if pywikibot is not fully imported (:phab:`T298384`)
* Use page.site.data_repository when creating a _WbDataPage (:phab:`T296985`)
* Fix mysql AttributeError for sock.close() on toolforge (:phab:`T216741`)
* Only search user_script_paths inside config.base_dir (:phab:`T296204`)
* pywikibot.argv has been fixed for pwb.py wrapper if called with global args (:phab:`T254435`)
* Only ignore FileExistsError when creating the api cache (:phab:`T295924`)
* Only handle query limit if query module is limited (:phab:`T294836`)
* Upload: Only set filekey/offset for files with names (:phab:`T294916`)
* Make site parameter of textlib.replace_links() mandatory (:phab:`T294649`)
* Raise a generic ServerError if the http status code is unofficial (:phab:`T293208`)

Breaking changes
^^^^^^^^^^^^^^^^

* Support of Python 3.5.0 - 3.5.2 has been dropped (:phab:`T286867`)
* generate_user_files.py, generate_user_files.py, shell.py and version.py were moved to pywikibot/scripts and must be used with pwb wrapper script
* *See also Code cleanups below*

Code cleanups
^^^^^^^^^^^^^

* Deprecated  http.get_fake_user_agent() function was removed
* FilePage.fileIsShared() was removed in favour of FilePage.file_is_shared()
* Page.canBeEdited() was removed in favour of Page.has_permission()
* BaseBot.stop() method were removed in favour of BaseBot.generator.close()
* showHelp() function was remove in favour of show_help
* CombinedPageGenerator pagegenerator was removed in favour of itertools.chain
* Remove deprecated echo.Notification.id
* Remove APISite.newfiles() method (:phab:`T168339`)
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
* Remove deprecated Page.put_async() method (:phab:`T193494`)
* Ignore baserevid parameter for several DataSite methods
* Remove deprecated preloaditempages method
* Remove disable_ssl_certificate_validation kwargs in http functions in favour of verify parameter (:phab:`T265206`)
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
* DuplicateFilterPageGenerator was replaced by :func:`tools.itertools.filter_unique`
* ItemPage.concept_url method was replaced by ItemPage.concept_uri
* Outdated parameter names has been dropped
* Deprecated pywikibot.Error exception were removed in favour of pywikibot.exceptions.Error classes (:phab:`T280227`)
* Deprecated exception identifiers were removed (:phab:`T280227`)
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


6.6.5
-----
*07 February 2022*

* L10N updates


6.6.4
-----
*27 January 2022*

* L10N updates


6.6.3
-----
*01 December 2021*

* L10N updates


6.6.2
-----
*28 October 2021*

* L10N updates (:phab:`T292423`, :phab:`T294526`, :phab:`T294527`)


6.6.1
-----
*21 September 2021*

* Fix for removed action API token parameters of MediaWiki 1.37 (:phab:`T291202`)
* APISite.validate_tokens() no longer replaces outdated tokens (:phab:`T291202`)
* L10N updates


6.6.0
-----
*15 September 2021*

* Drop piprop from meta=proofreadinfo API call (:phab:`T290585`)
* Remove use_2to3 with setup.py (:phab:`T290451`)
* Unify WbRepresentation's abstract method signature
* L10N updates


6.5.0
-----
*05 August 2021*

* Add support for jvwikisource (:phab:`T286247`)
* Handle missingtitle error code when deleting
* Check for outdated setuptools in pwb.py wrapper (:phab:`T286980`)
* Remove traceback for original exception for known API error codes
* Unused strm parameter of init_handlers was removed
* Ignore throttle.pid if a Site object cannot be created (:phab:`T286848`)
* Explicitly return an empty string with OutputProxyOption.out property (:phab:`T286403`)
* Explicitly return None from ContextOption.result() (:phab:`T286403`)
* Add support for Lingua Libre family (:phab:`T286303`)
* Catch invalid titles in Category.isCategoryRedirect()
* L10N updates
* Provide structured data on Commons (:phab:`T213904`, :phab:`T223820`)


6.4.0
-----
*01 July 2021*

* Add support for dagwiki, shiwiki and banwikisource
* Fix and clean up DataSite.get_property_by_name
* Update handling of abusefilter-{disallow,warning} codes (:phab:`T285317`)
* Fix terminal_interface_base.input_list_choice (:phab:`T285597`)
* Fix ItemPage.fromPage call
* Use \*iterables instead of genlist in intersect_generators
* Use a sentinel variable to determine the end of an iterable in roundrobin_generators
* Require setuptools 20.8.1 (:phab:`T284297`)
* Add setter and deleter for summary_parameters of AutomaticTWSummaryBot
* L10N updates
* Add update_options attribute to BaseBot class to update available_options
* Clear put_queue when canceling page save (:phab:`T284396`)
* Add -url option to pagegenerators (:phab:`T239436`)
* Add add_text function to textlib (:phab:`T284388`)
* Require setuptools >= 49.4.0 (:phab:`T284297`)
* Require wikitextparser>=0.47.5
* Allow images to upload locally even they exist in the shared repository (:phab:`T267535`)
* Show a warning if pywikibot.__version__ is behind scripts.__version__ (:phab:`T282766`)
* Handle <ce>/<chem> tags as <math> aliases within textlib.replaceExcept() (:phab:`T283990`)
* Expand simulate query response for wikibase support (:phab:`T76694`)
* Double the wait time if ratelimit exceeded (:phab:`T270912`)
* Deprecated extract_templates_and_params_mwpfh and extract_templates_and_params_regex functions were removed


6.3.0
-----
*31 May 2021*

* Check bot/nobots templates for cosmetic_changes hook (:phab:`T283989`)
* Remove outdated opt._option which is already dropped (:phab:`T284005`)
* Use IntEnum with cosmetic_changes CANCEL
* Remove lru_cache from botMayEdit method and fix it's logic (:phab:`T283957`)
* DataSite.createNewItemFromPage() method was removed in favour of ImagePage.fromPage() (:phab:`T98663`)
* mwparserfromhell or wikitextparser MediaWiki markup parser is mandatory (:phab:`T106763`)


6.2.0
-----
*28 May 2021*

Improvements and Bugfixes
^^^^^^^^^^^^^^^^^^^^^^^^^

* Use different logfiles for multiple processes of the same script (:phab:`T56685`)
* throttle.pip will be reused as soon as possbile
* terminal_interface_base.TerminalHandler is subclassed from logging.StreamHandler
* Fix iterating of SizedKeyCollection (:phab:`T282865`)
* An abstract base user interface module was added
* APISite method pagelanglinks() may skip links with empty titles (:phab:`T223157`)
* Fix Page.getDeletedRevision() method which always returned an empty list
* Async chunked uploads are supported (:phab:`T129216`, :phab:`T133443`)
* A new InvalidPageError will be raised if a Page has no version history (:phab:`T280043`)
* L10N updates
* Fix __getattr__ for WikibaseEntity (:phab:`T281389`)
* Handle abusefilter-{disallow,warning} codes (:phab:`T85656`)

Code cleanups
^^^^^^^^^^^^^

* MultipleSitesBot.site attribute was removed (:phab:`T283209`)
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
* pagenenerators.handleArg() method was renamed to handle_arg() (:phab:`T271437`)
* CategoryGenerator, FileGenerator, ImageGenerator and ReferringPageGenerator pagegenerator functions were removed
* Family.ignore_certificate_error() method was removed in favour of verify_SSL_certificate (:phab:`T265205`)
* tools.is_IP was renamed to is_ip_address due to :pep:`8`
* config2.py was renamed to config.py
* Exceptions were renamed having a suffix "Error" due to :pep:`8` (:phab:`T280227`)


6.1.0
-----
*17 April 2021*

Improvements and Bugfixes
^^^^^^^^^^^^^^^^^^^^^^^^^

* interwiki_graph module was restored (:phab:`T223826`)
* proofreadpage: search for "new" class after purge (:phab:`T280357`)
* Enable different types with BaseBot.treat()
* Context manager depends on pymysql version, not Python release (:phab:`T279753`)
* Bugfix for Site.interwiki_prefix() (:phab:`T188179`)
* Exclude expressions from parsed template in mwparserfromhell (:phab:`T71384`)
* Provide an object representation for DequeGenerator
* Allow deleting any subclass of BasePage by title (:phab:`T278659`)
* Add support for API:Revisiondelete with Site.deleterevs() method (:phab:`T276726`)
* L10N updates
* Family files can be collected from a zip folder (:phab:`T278076`)

Dependencies
^^^^^^^^^^^^

* **mwparserfromhell** or **wikitextparser** are strictly recommended (:phab:`T106763`)
* Require **Pillow**>=8.1.1 due to vulnerability found (:phab:`T278743`)
* TkDialog of GUI userinterface requires **Python 3.6+** (:phab:`T278743`)
* Enable textlib.extract_templates_and_params with **wikitextparser** package
* Add support for **PyMySQL** 1.0.0+

Code cleanups
^^^^^^^^^^^^^

* APISite.resolvemagicwords(), BaseSite.ns_index() and remove BaseSite.getNamespaceIndex() were removed
* Deprecated MoveEntry.new_ns() and new_title() methods were removed
* Unused NoSuchSite and PageNotSaved exception were removed
* Unused BadTitle exception was removed (:phab:`T267768`)
* getSite() function was removed in favour of Site() constructor
* Page.fileUrl() was removed in favour of Page.get_file_url()
* Deprecated getuserinfo and getglobaluserinfo Site methods were removed


6.0.1
-----
*20 March 2021*

* Add support for taywiki, trvwiki and mnwwiktionary (:phab:`T275838`, :phab:`T276128`, :phab:`T276250`)


6.0.0
-----
*16 March 2021*

Breaking changes
^^^^^^^^^^^^^^^^

* interwiki_graph module was removed (:phab:`T223826`)
* Require setuptools >= 20.2 due to :pep:`440`
* Support of MediaWiki < 1.23 has been dropped (:phab:`T268979`)
* APISite.loadimageinfo will no longer return any content
* Return requests.Response with http.request() instead of plain text (:phab:`T265206`)
* config.db_hostname has been renamed to db_hostname_format

Code cleanups
^^^^^^^^^^^^^

* tools.PY2 was removed (:phab:`T213287`)
* Site.language() method was removed in favour of Site.lang property
* Deprecated Page.getMovedTarget() method was removed in favour of moved_target()
* Remove deprecated Wikibase.lastrevid attribute
* config settings of archived scripts were removed (:phab:`T223826`)
* Drop startsort/endsort parameter for site.categorymembers method (:phab:`T74101`)
* Deprecated data attribute of http.fetch() result has been dropped (:phab:`T265206`)
* toStdout parameter of pywikibot.output() has been dropped
* Deprecated Site.getToken() and Site.case was removed
* Deprecated Family.known_families dict was removed (:phab:`T89451`)
* Deprecated DataSite.get_* methods was removed
* Deprecated LogEntryFactory.logtypes classproperty was removed
* Unused comms.threadedhttp module was removed; threadedhttp.HttpRequest was already replaced with requests.Response (:phab:`T265206`)

Other changes
^^^^^^^^^^^^^

* Raise a SiteDefinitionError if api request response is Non-JSON and site is AutoFamily (:phab:`T272911`)
* Support deleting and undeleting specific file versions (:phab:`T276725`)
* Only add bot option generator if the bot class have it already
* Raise a RuntimeError if pagegenerators -namespace option is provided too late (:phab:`T276916`)
* Check for LookupError exception in http._decide_encoding (:phab:`T276715`)
* Re-enable setting private family files (:phab:`T270949`)
* Move the hardcoded namespace identifiers to an IntEnum
* Buffer 'pageprops' in api.QueryGenerator
* Ensure that BaseBot.generator is a Generator
* Add additional info into log if 'messagecode' is missing during login (:phab:`T261061`, :phab:`T269503`)
* Use hardcoded messages if i18n system is not available (:phab:`T275981`)
* Move wikibase data structures to page/_collections.py
* L10N updates
* Add support for altwiki (:phab:`T271984`)
* Add support for mniwiki and mniwiktionary (:phab:`T273467`, :phab:`T273462`)
* Don't use mime parameter as boolean in api.Request (:phab:`T274723`)
* textlib.removeDisabledPart is able to remove templates (:phab:`T274138`)
* Create a SiteLink with __getitem__ method and implement lazy load (:phab:`T273386`, :phab:`T245809`, :phab:`T238471`, :phab:`T226157`)
* Fix date.formats['MonthName'] behaviour (:phab:`T273573`)
* Implement pagegenerators.handle_args() to process all options at once
* Add enabled_options, disabled_options to GeneratorFactory (:phab:`T271320`)
* Move interwiki() interwiki_prefix() and local_interwiki() methods from BaseSite to APISite
* Add requests.Response.headers to log when an API error occurs (:phab:`T272325`)


5.6.0
-----
*24 January 2021*

* Use string instead of Path-like object with "open" function in UploadRobot for Python 3.5 compatibility (:phab:`T272345`)
* Add support for trwikivoyage (:phab:`T271263`)
* UI.input_list_choice() has been improved (:phab:`T272237`)
* Global handleArgs() function was removed in favour of handle_args
* Deprecated originPage and foundIn property has been removed in interwiki_graph.py
* ParamInfo modules, prefixes, query_modules_with_limits properties and module_attribute_map() method was removed
* Allow querying alldeletedrevisions with APISite.alldeletedrevisions() and User.deleted_contributions()
* data attribute of http.fetch() response is deprecated (:phab:`T265206`)
* Positional arguments of page.Revision aren't supported any longer (:phab:`T259428`)
* pagenenerators.handleArg() method was renamed to handle_arg() (:phab:`T271437`)
* Page methods deprecated for 6 years were removed
* Create a Site with AutoFamily if a family isn't predefined (:phab:`T249087`)
* L10N updates


5.5.0
-----
*12 January 2021*

* Add support for niawiki, bclwikt, diqwikt, niawikt (:phab:`T270416`, :phab:`T270282`, :phab:`T270278`, :phab:`T270412`)
* Delete page using pageid instead of title (:phab:`T57072`)
* version.getversion_svn_setuptools function was removed (:phab:`T270393`)
* Add support for "musical notation" data type to wikibase
* -grepnot filter option was added to pagegenerators module (:phab:`T219281`)
* L10N updates


5.4.0
-----
*2 January 2021*

* Re-enable reading user-config.py from site package (:phab:`T270941`)
* LoginManager.getCookie() was renamed to login_to_site()
* Deprecation warning for MediaWiki < 1.23 (:phab:`T268979`)
* Add backports to support some Python 3.9 changes
* Desupported shared_image_repository() and nocapitalize() methods were removed (:phab:`T89451`)
* pywikibot.cookie_jar was removed in favour of pywikibot.comms.http.cookie_jar
* Align http.fetch() params with requests and rename 'disable_ssl_certificate_validation' to 'verify' (:phab:`T265206`)
* Deprecated compat BasePage.getRestrictions() method was removed
* Outdated Site.recentchanges() parameters has been dropped
* site.LoginStatus has been removed in favour of login.LoginStatus
* L10N Updates


5.3.0
-----
*19 December 2020*

* Allow using pywikibot as site-package without user-config.py (:phab:`T270474`)
* Python 3.10 is supported
* Fix AutoFamily scriptpath() call (:phab:`T270370`)
* Add support for skrwiki, skrwiktionary, eowikivoyage, wawikisource, madwiki (:phab:`T268414`, :phab:`T268460`, :phab:`T269429`, :phab:`T269434`, :phab:`T269442`)
* wikistats methods fetch, raw_cached, csv, xml has been removed
* PageRelatedError.getPage() has been removed in favour of PageRelatedError.page
* DataSite.get_item() method has been removed
* global put_throttle option may be given as float (:phab:`T269741`)
* Property.getType() method has been removed
* Family.server_time() method was removed; it is still available from Site object (:phab:`T89451`)
* All HttpRequest parameters except of charset has been dropped (:phab:`T265206`)
* A lot of methods and properties of HttpRequest are deprecared in favour of requests.Resonse attributes (:phab:`T265206`)
* Method and properties of HttpRequest are delegated to requests.Response object (:phab:`T265206`)
* comms.threadedhttp.HttpRequest.raw was replaced by HttpRequest.content property (:phab:`T265206`)
* Desupported version.getfileversion() has been removed
* site parameter of comms.http.requests() function is mandatory and cannot be omitted
* date.MakeParameter() function has been removed
* api.Request.http_params() method has been removed
* L10N updates


5.2.0
-----
*10 December 2020*

* Remove deprecated args for Page.protect() (:phab:`T227610`)
* Move BaseSite its own site/_basesite.py file
* Improve toJSON() methods in page.__init__.py
* _is_wikibase_error_retryable rewritten (:phab:`T48535`, 268645)
* Replace FrozenDict with frozenmap
* WikiStats table may be sorted by any key
* Retrieve month names from mediawiki_messages when required
* Move Namespace and NamespacesDict to site/_namespace.py file
* Fix TypeError in api.LoginManager (:phab:`T268445`)
* Add repr() method to BaseDataDict and ClaimCollection
* Define availableOptions as deprecated property
* Do not strip all whitespaces from Link.title (:phab:`T197642`)
* Introduce a common BaseDataDict as parent for LanguageDict and AliasesDict
* Replaced PageNotSaved by PageSaveRelatedError (:phab:`T267821`)
* Add -site option as -family -lang shortcut
* Enable APISite.exturlusage() with default parameters (:phab:`T266989`)
* Update tools._unidata._category_cf from Unicode version 13.0.0
* Move TokenWallet to site/_tokenwallet.py file
* Fix import of httplib after release of requests 2.25 (:phab:`T267762`)
* user keyword parameter can be passed to Site.rollbackpage() (:phab:`T106646`)
* Check for {{bots}}/{{nobots}} templates in Page.text setter (:phab:`T262136`, :phab:`T267770`)
* Remove deprecated UserBlocked exception and Page.contributingUsers()
* Add support for some 'wbset' actions in DataSite
* Fix UploadRobot site attribute (:phab:`T267573`)
* Ignore UnicodeDecodeError on input (:phab:`T258143`)
* Replace 'source' exception regex with 'syntaxhighlight' (:phab:`T257899`)
* Fix get_known_families() for wikipedia_family (:phab:`T267196`)
* Move _InterwikiMap class to site/_interwikimap.py
* instantiate a CosmeticChangesToolkit by passing a page
* Create a Site from sitename
* pywikibot.Site() parameters "interface" and "url" must be keyworded
* Lookup the code parameter in xdict first (:phab:`T255917`)
* Remove interwiki_forwarded_from list from family files (:phab:`T104125`)
* Rewrite Revision class; each data can be accessed either by key or as an attribute (:phab:`T102735`, :phab:`T259428`)
* L10N-Updates


5.1.0
-----

*1 November 2020*

* Avoid conflicts between site and possible site keyword in api.Request.create_simple() (:phab:`T262926`)
* Remove wrong param of rvision() call in Page.latest_revision_id
* Do not raise Exception in Page.get_best_claim() but follow redirect (:phab:`T265839`)
* xml-support of wikistats will be dropped
* Remove deprecated mime_params in api.Request()
* cleanup interwiki_graph.py and replace deprecated originPage by origin in Subjects
* Upload a file that ends with the '\r' byte (:phab:`T132676`)
* Fix incorrect server time (:phab:`T266084`)
* L10N-Updates
* Support Namespace packages in version.py (:phab:`T265946`)
* Server414Error was added to pywikibot (:phab:`T266000`)
* Deprecated editor.command() method was removed
* comms.PywikibotCookieJar and comms.mode_check_decorator were deleted
* Remove deprecated tools classes Stringtypes and UnicodeType
* Remove deprecated tools function open_compressed and signature and UnicodeType class
* Fix http_tests.LiveFakeUserAgentTestCase (:phab:`T265842`)
* HttpRequest properties were renamed to request.Response identifiers (:phab:`T265206`)


5.0.0
-----

*19 October 2020*

* Add support for smn-wiki (:phab:`T264962`)
* callback parameter of comms.http.fetch() is desupported
* Fix api.APIError() calls for Flow and Thanks extension
* edit, move, create, upload, unprotect and prompt parameters of Page.protect() are deprecated (:phab:`T227610`)
* Accept only valid names in generate_family_file.py (:phab:`T265328`, :phab:`T265353`)
* New plural.plural_rule() function returns a rule for a given language
* Replace deprecated urllib.request.URLopener with http.fetch (:phab:`T255575`)
* OptionHandler/BaseBot options are accessable as OptionHandler.opt attributes or keyword item (see also :phab:`T264721`)
* pywikibot.setAction() function was removed
* A namedtuple is the result of textlib.extract_sections()
* Prevent circular imports in config2.py and http.py (:phab:`T264500`)
* version.get_module_version() is deprecated and gives no meaningfull result
* Fix version.get_module_filename() and update log lines (:phab:`T264235`)
* Re-enable printing log header (:phab:`T264235`)
* Fix result of :func:`tools.itertools.intersect_generators` (:phab:`T263947`)
* Only show _GLOBAL_HELP options if explicitly wanted
* Deprecated Family.version() methods were removed
* Unused parameters of page methods like forceReload, insite, throttle, step was removed
* Raise RuntimeError instead of AttributeError for old wikis (:phab:`T263951`)
* Deprecated script options were removed
* lyricwiki_family was removed (:phab:`T245439`)
* RecentChangesPageGenerator parameters has been synced with APISite.recentchanges
* APISite.recentchanges accepts keyword parameters only
* LoginStatus enum class was moved from site to login.py
* WbRepresentation derives from abstract base class abc.ABC
* Update characters in the Cf category to Unicode version 12.1.0
* Update __all__ variable in pywikibot (:phab:`T122879`)
* Use api.APIGenerator through site._generator (:phab:`T129013`)
* Support of MediaWiki releases below 1.19 has been dropped (:phab:`T245350`)
* Page.get_best_claim () retrieves preferred Claim of a property referring to the given page (:phab:`T175207`)
* Check whether _putthead is current_thread() to join() (:phab:`T263331`)
* Add BasePage.has_deleted_revisions() method
* Allow querying deleted revs without the deletedhistory right
* Use ignore_discard for login cookie container (:phab:`T261066`)
* Siteinfo.get() loads data via API instead from cache if expiry parameter is True (:phab:`T260490`)
* Move latest revision id handling to WikibaseEntity (:phab:`T233406`)
* Load wikibase entities when necessary (:phab:`T245809`)
* Fix path for stable release in version.getversion() (:phab:`T262558`)
* "since" parameter in EventStreams given as Timestamp or MediaWiki timestamp string has been fixed
* Methods deprecated for 6 years or longer were removed
* Page.getVersionHistory and Page.fullVersionHistory() methods were removed (:phab:`T136513`, :phab:`T151110`)
* Allow multiple types of contributors parameter given for Page.revision_count()
* Deprecated tools.UnicodeMixin and tools.IteratorNextMixin has been removed
* Localisation updates


4.3.0
-----

*2 September 2020*

* Don't check for valid Family/Site if running generate_user_files.py (:phab:`T261771`)
* Remove socket_timeout fix in config2.py introduced with :phab:`T103069`
* Prevent huge traceback from underlying python libraries (:phab:`T253236`)
* Localisation updates


4.2.0
-----

*28 August 2020*

* Add support for ja.wikivoyage (:phab:`T261450`)
* Only run cosmetic changes on wikitext pages (:phab:`T260489`)
* Leave a script gracefully for wrong -lang and -family option (:phab:`T259756`)
* Change meaning of BasePage.text (:phab:`T260472`)
* site/family methods code2encodings() and code2encoding() has been removed in favour of encoding()/encodings() methods
* Site.getExpandedString() method was removed in favour of expand_text
* Site.Family() function was removed in favour of Family.load() method
* Add wikispore family (:phab:`T260049`)


4.1.1
-----

*18 August 2020*

* Add support for lldwiki to Pywikibot
* Fix getversion_git subprocess command


4.1.0
-----

*16 August 2020*

* Enable Pywikibot for Python 3.9
* APISite.loadpageinfo does not discard changes to page content when information was not loaded (:phab:`T260472`)
* tools.UnicodeType and tools.signature are deprecated
* BaseBot.stop() method is deprecated in favour of BaseBot.generator.close()
* Escape bot password correctly (:phab:`T259488`)
* Bugfixes and improvements
* Localisation updates


4.0.0
-----

*4 August 2020*

* Read correct object in SiteLinkCollection.normalizeData (:phab:`T259426`)
* tools.count and tools classes Counter, OrderedDict and ContextManagerWrapper were removed
* Deprecate UnicodeMixin and IteratorNextMixin
* Restrict site module interface
* EventStreams "since" parameter settings has been fixed
* Unsupported debug and uploadByUrl parameters of UploadRobot were removed
* Unported compat decode parameter of Page.title() has been removed
* Wikihow family file was added (:phab:`T249814`)
* Improve performance of CosmeticChangesToolkit.translateMagicWords
* Prohibit positional arguments with Page.title()
* Functions dealing with stars list were removed
* Some pagegenerators functions were deprecated which should be replaced by site generators
* LogEntry became a UserDict; all content can be accessed by its key
* URLs for new toolforge.org domain were updated
* pywikibot.__release__ was deprecated
* Use one central point for framework version (:phab:`T106121`, :phab:`T171886`, :phab:`T197936`, :phab:`T253719`)
* rvtoken parameter of Site.loadrevisions() and Page.revisions() has been dropped (:phab:`T74763`)
* getFilesFromAnHash and getImagesFromAnHash Site methods have been removed
* Site and Page methods deprecated for 10 years or longer have been removed
* Support for Python 2 and 3.4 has been dropped (:phab:`T213287`, :phab:`T239542`)
* Bugfixes and improvements
* Localisation updates


3.0.20200703
------------

*3 July 2020*

* Page.botMayEdit() method was improved (:phab:`T253709`)
* PageNotFound, SpamfilterError, UserActionRefuse exceptions were removed (:phab:`T253681`)
* tools.ip submodule has been removed (:phab:`T243171`)
* Wait in BaseBot.exit() until asynchronous saving pages are completed
* Solve IndexError when showing an empty diff with a non-zero context (:phab:`T252724`)
* linktrails were added or updated for a lot of sites
* Resolve namespaces with underlines (:phab:`T252940`)
* Fix getversion_svn for Python 3.6+ (:phab:`T253617`, :phab:`T132292`)
* Bugfixes and improvements
* Localisation updates


3.0.20200609
------------

*9 June 2020*

* Fix page_can_be_edited for MediaWiki < 1.23 (:phab:`T254623`)
* Show global options with pwb.py -help
* Usage of SkipPageError with BaseBot has been removed
* Throttle requests after ratelimits exceeded (:phab:`T253180`)
* Make Pywikibot daemon logs unexecutable (:phab:`T253472`)
* Check for missing generator after BaseBot.setup() call
* Do not change usernames when creating a Site (:phab:`T253127`)
* pagegenerators: handle protocols in -weblink (:phab:`T251308`, :phab:`T251310`)
* Bugfixes and improvements
* Localisation updates


3.0.20200508
------------

*8 May 2020*

* Unify and extend formats for setting sitelinks (:phab:`T225863`, :phab:`T251512`)
* Do not return a random i18n.translation() result (:phab:`T220099`)
* tools.ip_regexp has been removed (:phab:`T174482`)
* Page.getVersionHistory and Page.fullVersionHistory() methods has been desupported (:phab:`T136513`, :phab:`T151110`)
* Update wikimediachapter_family (:phab:`T250802`)
* Raise SpamblacklistError with spamblacklist APIError (:phab:`T249436`)
* SpamfilterError was renamed to SpamblacklistError (:phab:`T249436`)
* Do not removeUselessSpaces inside source/syntaxhighlight tags (:phab:`T250469`)
* Restrict Pillow to 6.2.2+ (:phab:`T249911`)
* Fix PetScan generator language and project (:phab:`T249704`)
* test_family has been removed (:phab:`T228375`, :phab:`T228300`)
* Bugfixes and improvements
* Localisation updates

3.0.20200405
------------

*5 April 2020*

* Fix regression of combining sys.path in pwb.py wrapper (:phab:`T249427`)
* Site and Page methods deprecated for 10 years or longer are desupported and may be removed (:phab:`T106121`)
* Usage of SkipPageError with BaseBot is desupported and may be removed
* Ignore InvalidTitle in textlib.replace_links() (:phab:`T122091`)
* Raise ServerError also if connection to PetScan timeouts
* pagegenerators.py no longer supports 'oursql' or 'MySQLdb'. It now solely supports PyMySQL (:phab:`T243154`, :phab:`T89976`)
* Disfunctional Family.versionnumber() method was removed
* Refactor login functionality (:phab:`T137805`, :phab:`T224712`, :phab:`T248767`, :phab:`T248768`, :phab:`T248945`)
* Bugfixes and improvements
* Localisation updates

3.0.20200326
------------

*26 March 2020*

* site.py and page.py files were moved to their own folders and will be split in the future
* Refactor data attributes of Wikibase entities (:phab:`T233406`)
* Functions dealing with stars list are desupported and may be removed
* Use path's stem of script filename within pwb.py wrapper (:phab:`T248372`)
* Disfunctional cgi_interface.py was removed (:phab:`T248292`, :phab:`T248250`, :phab:`T193978`)
* Fix logout on MW < 1.24 (:phab:`T214009`)
* Fixed TypeError in getFileVersionHistoryTable method (:phab:`T248266`)
* Outdated secure connection overrides were removed (:phab:`T247668`)
* Check for all modules which are needed by a script within pwb.py wrapper
* Check for all modules which are mandatory within pwb.py wrapper script
* Enable -help option with similar search of pwb.py (:phab:`T241217`)
* compat module has been removed (:phab:`T183085`)
* Category.copyTo and Category.copyAndKeep methods have been removed
* Site.page_restrictions() does no longer raise NoPage (:phab:`T214286`)
* Use site.userinfo getter instead of site._userinfo within api (:phab:`T243794`)
* Fix endprefix parameter in Category.articles() (:phab:`T247201`)
* Fix search for changed claims when saving entity (:phab:`T246359`)
* backports.py has been removed (:phab:`T244664`)
* Site.has_api method has been removed (:phab:`T106121`)
* Bugfixes and improvements
* Localisation updates

3.0.20200306
------------

*6 March 2020*

* Fix mul Wikisource aliases (:phab:`T242537`, :phab:`T241413`)
* Let Site('test', 'test) be equal to Site('test', 'wikipedia') (:phab:`T228839`)
* Support of MediaWiki releases below 1.19 will be dropped (:phab:`T245350`)
* Provide mediawiki_messages for foreign language codes
* Use mw API IP/anon user detection (:phab:`T245318`)
* Correctly choose primary coordinates in BasePage.coordinates() (:phab:`T244963`)
* Rewrite APISite.page_can_be_edited (:phab:`T244604`)
* compat module is deprecated for 5 years and will be removed in next release (:phab:`T183085`)
* ipaddress module is required for Python 2 (:phab:`T243171`)
* tools.ip will be dropped in favour of tools.is_IP (:phab:`T243171`)
* tools.ip_regexp is deprecatd for 5 years and will be removed in next release
* backports.py will be removed in next release (:phab:`T244664`)
* stdnum package is required for ISBN scripts and cosmetic_changes (:phab:`T132919`, :phab:`T144288`, :phab:`T241141`)
* preload urllib.quote() with Python 2 (:phab:`T243710`, :phab:`T222623`)
* Drop isbn_hyphenate package due to outdated data (:phab:`T243157`)
* Fix UnboundLocalError in ProofreadPage._ocr_callback (:phab:`T243644`)
* Deprecate/remove sysop parameter in several methods and functions
* Refactor Wikibase entity namespace handling (:phab:`T160395`)
* Site.has_api method will be removed in next release
* Category.copyTo and Category.copyAndKeep will be removed in next release
* weblib module has been removed (:phab:`T85001`)
* botirc module has been removed (:phab:`T212632`)
* Bugfixes and improvements
* Localisation updates

3.0.20200111
------------

*11 January 2020*

* Fix broken get_version() in setup.py (:phab:`T198374`)
* Rewrite site.log_page/site.unlock_page implementation
* Require requests 2.20.1 (:phab:`T241934`)
* Make bot.suggest_help a function
* Fix gui settings for Python 3.7.4+ (:phab:`T241216`)
* Better api error message handling (:phab:`T235500`)
* Ensure that required props exists as Page attribute (:phab:`T237497`)
* Refactor data loading for WikibaseEntities (:phab:`T233406`)
* replaceCategoryInPlace: Allow LRM and RLM at the end of the old_cat title (:phab:`T240084`)
* Support for Python 3.4 will be dropped (:phab:`T239542`)
* Derive LoginStatus from IntEnum (:phab:`T213287`, :phab:`T239533`)
* enum34 package is mandatory for Python 2.7 (:phab:`T213287`)
* call LoginManager with keyword arguments (:phab:`T237501`)
* Enable Pywikibot for Python 3.8 (:phab:`T238637`)
* Derive BaseLink from tools.UnicodeMixin (:phab:`T223894`)
* Make _flush aware of _putthread ongoing tasks (:phab:`T147178`)
* Add family file for foundation wiki (:phab:`T237888`)
* Fix generate_family_file.py for private wikis (:phab:`T235768`)
* Add rank parameter to Claim initializer
* Add current directory for similar script search (:phab:`T217195`)
* Release BaseSite.lock_page mutex during sleep
* Implement deletedrevisions api call (:phab:`T75370`)
* assert_valid_iter_params may raise AssertionError instead of pywikibot.Error (:phab:`T233582`)
* Upcast getRedirectTarget result and return the appropriate page subclass (:phab:`T233392`)
* Add ListGenerator for API:filearchive to site module (:phab:`T230196`)
* Deprecate the ability to login with a secondary sysop account (:phab:`T71283`)
* Enable global args with pwb.py wrapper script (:phab:`T216825`)
* Add a new ConfigParserBot class to set options from the scripts.ini file (:phab:`T223778`)
* Check a user's rights rather than group memberships; 'sysopnames' will be deprecated (:phab:`T229293`, :phab:`T189126`, :phab:`T122705`, :phab:`T119335`, :phab:`T75545`)
* proofreadpage.py: fix footer detection (:phab:`T230301`)
* Add allowusertalk to the User.block() options (:phab:`T229288`)
* botirc module will be removed in next release (:phab:`T212632`)
* weblib module will be removed in next release (:phab:`T85001`)
* Bugfixes and improvements
* Localisation updates

3.0.20190722
------------

*22 July 2019*

* Increase the throttling delay if maxlag >> retry-after (:phab:`T210606`)
* deprecate test_family: Site('test', 'test'), use wikipedia_family: Site('test', 'wikipedia') instead (:phab:`T228375`, :phab:`T228300`)
* Add "user_agent_description" option in config.py
* APISite.fromDBName works for all known dbnames (:phab:`T225590`, 225723, 226960)
* remove the unimplemented "proxy" variable in config.py
* Make Family.langs property more robust (:phab:`T226934`)
* Remove strategy family
* Handle closed_wikis as read-only (:phab:`T74674`)
* TokenWallet: login automatically
* Add closed_wikis to Family.langs property (:phab:`T225413`)
* Redirect 'mo' site code to 'ro' and remove interwiki_replacement_overrides (:phab:`T225417`, :phab:`T89451`)
* Add support for badges on Wikibase item sitelinks through a SiteLink object instead plain str (:phab:`T128202`)
* Remove login.showCaptchaWindow() method
* New parameter supplied in suggest_help function for missing dependencies
* Remove NonMWAPISite class
* Introduce Claim.copy and prevent adding already saved claims (:phab:`T220131`)
* Fix create_short_link method after MediaWiki changes (:phab:`T223865`)
* Validate proofreadpage.IndexPage contents before saving it
* Refactor Link and introduce BaseLink (:phab:`T66457`)
* Count skipped pages in BaseBot class
* 'actionthrottledtext' is a retryable wikibase error (:phab:`T192912`)
* Clear tokens on logout(:phab:`T222508`)
* Deprecation warning: support for Python 2 will be dropped (:phab:`T213287`)
* botirc.IRCBot has been dropped
* Avoid using outdated browseragents (:phab:`T222959`)
* textlib: avoid infinite execution of regex (:phab:`T222671`)
* Add CSRF token in sitelogout() api call (:phab:`T222508`)
* Refactor WikibasePage.get and overriding methods and improve documentation
* Improve title patterns of WikibasePage extensions
* Add support for property creation (:phab:`T160402`)
* Bugfixes and improvements
* Localisation updates

3.0.20190430
------------

*30 April 2019*

* Unicode literals are required for all scripts; the usage of ASCII bytes may fail (:phab:`T219095`)
* Don't fail if the number of forms of a plural string is less than required (:phab:`T99057`, :phab:`T219097`)
* Implement create_short_link Page method to use Extension:UrlShortener (:phab:`T220876`)
* Remove wikia family file (:phab:`T220921`)
* Remove deprecated ez_setup.py
* Changed requirements for sseclient (:phab:`T219024`)
* Set optional parameter namespace to None in site.logpages (:phab:`T217664`)
* Add ability to display similar scripts when misspelled (:phab:`T217195`)
* Check if QueryGenerator supports namespaces (:phab:`T198452`)
* Bugfixes and improvements
* Localisation updates

3.0.20190301
------------

*1 March 2019*

* Fix version comparison (:phab:`T164163`)
* Remove pre MediaWiki 1.14 code
* Dropped support for Python 2.7.2 and 2.7.3 (:phab:`T191192`)
* Fix header regex beginning with a comment (:phab:`T209712`)
* Implement Claim.__eq__ (:phab:`T76615`)
* cleanup config2.py
* Add missing Wikibase API write actions
* Bugfixes and improvements
* Localisation updates

3.0.20190204
------------

*4 February 2019*

* Support python version 3.7
* pagegenerators.py: add -querypage parameter to yield pages provided by any special page (:phab:`T214234`)
* Fix comparison of str, bytes and int literal
* site.py: add generic self.querypage() to query SpecialPages
* echo.Notification has a new event_id property as integer
* Bugfixes and improvements
* Localisation updates

3.0.20190106
------------

*6 January 2019*

* Ensure "modules" parameter of ParamInfo._fetch is a set (:phab:`T122763`)
* Support adding new claims with qualifiers and/or references (:phab:`T112577`, :phab:`T170432`)
* Support LZMA and XZ compression formats
* Update correct-ar Typo corrections in fixes.py (:phab:`T211492`)
* Enable MediaWiki timestamp with EventStreams (:phab:`T212133`)
* Convert Timestamp.fromtimestampformat() if year, month and day are given only
* tools.concat_options is deprecated
* Additional ListOption subclasses ShowingListOption, MultipleChoiceList, ShowingMultipleChoiceList
* Bugfixes and improvements
* Localisation updates

3.0.20181203
------------

*3 December 2018*

* Remove compat module references from autogenerated docs (:phab:`T183085`)
* site.preloadpages: split pagelist in most max_ids elements (:phab:`T209111`)
* Disable empty sections in cosmetic_changes for user namespace
* Prevent touch from re-creating pages (:phab:`T193833`)
* New Page.title() parameter without_brackets; also used by titletranslate (:phab:`T200399`)
* Security: require requests version 2.20.0 or later (:phab:`T208296`)
* Check appropriate key in Site.messages (:phab:`T163661`)
* Make sure the cookie file is created with the right permissions (:phab:`T206387`)
* pydot >= 1.2 is required for interwiki_graph
* Move methods for simple claim adding/removing to WikibasePage (:phab:`T113131`)
* Enable start timestamp for EventStreams (:phab:`T205121`)
* Re-enable notifications (:phab:`T205184`)
* Use FutureWarning for warnings intended for end users (:phab:`T191192`)
* Provide new -wanted... page generators (:phab:`T56557`, :phab:`T150222`)
* api.QueryGenerator: Handle slots during initialization (:phab:`T200955`, :phab:`T205210`)
* Bugfixes and improvements
* Localisation updates

3.0.20180922
------------

*22 September 2018*

* Enable multiple streams for EventStreams (:phab:`T205114`)
* Fix Wikibase aliases handling (:phab:`T194512`)
* Remove cryptography support from python<=2.7.6 requirements (:phab:`T203435`)
* textlib._tag_pattern: Do not mistake self-closing tags with start tag (:phab:`T203568`)
* page.Link.langlinkUnsafe: Always set _namespace to a Namespace object (:phab:`T203491`)
* Enable Namespace.content for mw < 1.16
* Allow terminating the bot generator by BaseBot.stop() method (:phab:`T198801`)
* Allow bot parameter in set_redirect_target
* Do not show empty error messages (:phab:`T203462`)
* Show the exception message in async mode (:phab:`T203448`)
* Fix the extended user-config extraction regex (:phab:`T145371`)
* Solve UnicodeDecodeError in site.getredirtarget (:phab:`T126192`)
* Introduce a new APISite property: mw_version
* Improve hash method for BasePage and Link
* Avoid applying two uniquifying filters (:phab:`T199615`)
* Fix skipping of language links in CosmeticChangesToolkit.removeEmptySections (:phab:`T202629`)
* New mediawiki projects were provided
* Bugfixes and improvements
* Localisation updates

3.0.20180823
------------

*23 August 2018*

* Don't reset Bot._site to None if we have already a site object (:phab:`T125046`)
* pywikibot.site.Siteinfo: Fix the bug in cache_time when loading a CachedRequest (:phab:`T202227`)
* pagegenerators._handle_recentchanges: Do not request for reversed results (:phab:`T199199`)
* Use a key for filter_unique where appropriate (:phab:`T199615`)
* pywikibot.tools: Add exceptions for first_upper (:phab:`T200357`)
* Fix usages of site.namespaces.NAMESPACE_NAME (:phab:`T201969`)
* pywikibot/textlib.py: Fix header regex to allow comments
* Use 'rvslots' when fetching revisions on MW 1.32+ (:phab:`T200955`)
* Drop the '2' from PYWIKIBOT2_DIR, PYWIKIBOT2_DIR_PWB, and PYWIKIBOT2_NO_USER_CONFIG environment variables. The old names are now deprecated. The other PYWIKIBOT2_* variables which were used only for testing purposes have been renamed without deprecation. (:phab:`T184674`)
* Introduce a timestamp in deprecated decorator (:phab:`T106121`)
* textlib.extract_sections: Remove footer from the last section (:phab:`T199751`)
* Don't let WikidataBot crash on save related errors (:phab:`T199642`)
* Allow different projects to have different L10N entries (:phab:`T198889`)
* remove color highlights before fill function (:phab:`T196874`)
* Fix Portuguese file namespace translation in cc (:phab:`T57242`)
* textlib._create_default_regexes: Avoid using inline flags (:phab:`T195538`)
* Not everything after a language link is footer (:phab:`T199539`)
* code cleanups
* New mediawiki projects were provided
* Bugfixes and improvements
* Localisation updates

3.0.20180710
------------

*10 July 2018*

* Enable any LogEntry subclass for each logevent type (:phab:`T199013`)
* Deprecated pagegenerators options -<logtype>log aren't supported any longer (:phab:`T199013`)
* Open RotatingFileHandler with utf-8 encoding (:phab:`T188231`)
* Fix occasional failure of TestLogentries due to hidden namespace (:phab:`T197506`)
* Remove multiple empty sections at once in cosmetic_changes (:phab:`T196324`)
* Fix stub template position by putting it above interwiki comment (:phab:`T57034`)
* Fix handling of API continuation in PropertyGenerator (:phab:`T196876`)
* Use PyMySql as pure-Python MySQL client library instead of oursql, deprecate MySQLdb (:phab:`T89976`, :phab:`T142021`)
* Ensure that BaseBot.treat is always processing a Page object (:phab:`T196562`, :phab:`T196813`)
* Update global bot settings
* New mediawiki projects were provided
* Bugfixes and improvements
* Localisation updates

3.0.20180603
------------

*3 June 2018*

* Move main categories to top in cosmetic_changes
* shell.py always imports pywikibot as default
* New roundrobin_generators in tools
* New BaseBot method "skip_page" to adjust page counting
* Family class is made a singleton class
* New rule 'startcolon' was introduced in textlib
* BaseBot has new methods setup and teardown
* UploadBot got a filename prefix parameter (:phab:`T170123`)
* cosmetic_changes is able to remove empty sections (:phab:`T140570`)
* Pywikibot is following :pep:`396` versioning
* pagegenerators AllpagesPageGenerator, CombinedPageGenerator, UnconnectedPageGenerator are deprecated
* Some DayPageGenerator parameters has been renamed
* unicodedata2, httpbin and Flask dependency was removed (:phab:`T102461`, :phab:`T108068`, :phab:`T178864`, :phab:`T193383`)
* New projects were provided
* Bugfixes and improvements
* Documentation updates
* Localisation updates (:phab:`T194893`)
* Translation updates

3.0.20180505
------------

*5 May 2018*

* Enable makepath and datafilepath not to create the directory
* Use API's retry-after value (:phab:`T144023`)
* Provide startprefix parameter for Category.articles() (:phab:`T74101`, :phab:`T143120`)
* Page.put_async() is marked as deprecated (:phab:`T193494`)
* Deprecate requests-requirements.txt (:phab:`T193476`)
* Bugfixes and improvements
* New mediawiki projects were provided
* Localisation updates

3.0.20180403
------------

*3 April 2018*

* Deprecation warning: support for Python 2.7.2 and 2.7.3 will be dropped (:phab:`T191192`)
* Dropped support for Python 2.6 (:phab:`T154771`)
* Dropped support for Python 3.3 (:phab:`T184508`)
* Bugfixes and improvements
* Localisation updates

3.0.20180304
------------

*4 March 2018*

* Bugfixes and improvements
* Localisation updates

3.0.20180302
------------

*2 March 2018*

* Changed requirements for requests and sseclient
* Bugfixes and improvements
* Localisation updates

3.0.20180204
------------

*4 February 2018*

* Deprecation warning: support for py2.6 and py3.3 will be dropped
* Changed requirements for cryprography, Pillow and pyOpenSSL
* Bugfixes and improvements
* Localisation updates

3.0.20180108
------------

*8 January 2018*

* Maintenance script to download Wikimedia database dump
* Option to auto-create accounts when logging in
* Ship wikimania family file
* Drop battlestarwiki family file
* Bugfixes and improvements
* Localisation updates

3.0.20171212
------------

*12 December 2017*

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

*1 August 2017*

* Bugfixes and improvements
* Localisation updates

3.0.20170713
------------

*13 July 2017*

* Deprecate APISite.newfiles()
* Inverse of pagegenerators -namespace option
* Bugfixes and improvements
* Localisation updates
* CODE_OF_CONDUCT included

Bugfixes
^^^^^^^^
* Manage temporary readonly error (:phab:`T154011`)
* Unbreak wbGeoShape and WbTabularData (:phab:`T166362`)
* Clean up issue with _WbDataPage (:phab:`T166362`)
* Re-enable xml for WikiStats with py2 (:phab:`T165830`)
* Solve httplib.IncompleteRead exception in eventstreams (:phab:`T168535`)
* Only force input_choise if self.always is given (:phab:`T161483`)
* Add colon when replacing category and file weblink (:phab:`T127745`)
* API Request: set uiprop only when ensuring 'userinfo' in meta (:phab:`T169202`)
* Fix TestLazyLoginNotExistUsername test for Stewardwiki (:phab:`T169458`)

Improvements
^^^^^^^^^^^^
* Introduce the new WbUnknown data type for Wikibase (:phab:`T165961`)
* djvu.py: add replace_page() and delete_page()
* Build GeoShape and TabularData from shared base class
* Remove non-breaking spaces when tidying up a link (:phab:`T130818`)
* Replace private mylang variables with mycode in generate_user_files.py
* FilePage: remove deprecated use of fileUrl
* Make socket_timeout recalculation reusable (:phab:`T166539`)
* FilePage.download(): add revision parameter to download arbitrary revision (:phab:`T166939`)
* Make pywikibot.Error more precise (:phab:`T166982`)
* Implement pywikibot support for adding thanks to normal revisions (:phab:`T135409`)
* Implement server side event client EventStreams (:phab:`T158943`)
* new pagegenerators filter option -titleregexnot
* Add exception for -namepace option (:phab:`T167580`)
* InteractiveReplace: Allow no replacements by default
* Encode default globe in family file
* Add on to pywikibot support for thanking normal revisions (:phab:`T135409`)
* Add log entry code for thanks log (:phab:`T135413`)
* Create superclass for log entries with user targets
* Use relative reference to class attribute
* Allow pywikibot to authenticate against a private wiki (:phab:`T153903`)
* Make WbRepresentations hashable (:phab:`T167827`)

Updates
^^^^^^^
* Update linktails
* Update languages_by_size
* Update cross_allowed (global bot wikis group)
* Add atjwiki to wikipedia family file (:phab:`T168049`)
* remove closed sites from languages_by_size list
* Update category_redirect_templates for wikipedia and commons Family
* Update logevent type parameter list
* Disable cleanUpSectionHeaders on jbo.wiktionary (:phab:`T168399`)
* Add kbpwiki to wikipedia family file (:phab:`T169216`)
* Remove anarchopedia family out of the framework (:phab:`T167534`)

3.0.20170521
------------

*21 May 2017*

* Support for Python 2.6 but higher releases are strictly recommended
* Bugfixes and improvements
* Localisation updates

Bugfixes
^^^^^^^^
* Increase the default socket_timeout to 75 seconds (:phab:`T163635`)
* use repr() of exceptions to prevent UnicodeDecodeErrors (:phab:`T120222`)
* Handle offset mismatches during chunked upload (:phab:`T156402`)
* Correct _wbtypes equality comparison (:phab:`T160282`)
* Re-enable getFileVersionHistoryTable() method (:phab:`T162528`)
* Replaced the word 'async' with 'asynchronous' due to py3.7 (:phab:`T106230`)
* Raise ImportError if no editor is available (:phab:`T163632`)
* templatesWithParams: cache and standardise params (:phab:`T113892`)
* getInternetArchiveURL: Retry http.fetch if there is a ConnectionError (:phab:`T164208`)
* Remove wikidataquery from pywikibot (:phab:`T162585`)

Improvements
^^^^^^^^^^^^
* Introduce user_add_claim and allow asynchronous ItemPage.addClaim (:phab:`T87493`)
* Enable private edit summary in specialbots (:phab:`T162527`)
* Make a decorator for asynchronous methods
* Provide options by a separate handler class
* Show a warning when a LogEntry type is not known (:phab:`T135505`)
* Add Wikibase Client extension requirement to APISite.unconnectedpages()
* Update content after editing entity
* Make WbTime from Timestamp and vice versa (:phab:`T131624`)
* Add support for geo-shape Wikibase data type (:phab:`T161726`)
* Add async parameter to ItemPage.editEntity (:phab:`T86074`)
* Make sparql use Site to access sparql endpoint and entity_url (:phab:`T159956`)
* timestripper: search wikilinks to reduce false matches
* Set Coordinate globe via item
* use extract_templates_and_params_regex_simple for template validation
* Add _items for WbMonolingualText
* Allow date-versioned pypi releases from setup.py (:phab:`T152907`)
* Provide site to WbTime via WbTime.fromWikibase
* Provide preloading via GeneratorFactory.getCombinedGenerator() (:phab:`T135331`)
* Accept QuitKeyboardInterrupt in specialbots.Uploadbot (:phab:`T163970`)
* Remove unnecessary description change message when uploading a file (:phab:`T163108`)
* Add 'OptionHandler' to bot.__all__ tuple
* Use FilePage.upload inside UploadRobot
* Add support for tabular-data Wikibase data type (:phab:`T163981`)
* Get thumburl information in FilePage() (:phab:`T137011`)

Updates
^^^^^^^
* Update languages_by_size in family files
* wikisource_family.py: Add "pa" to languages_by_size
* Config2: limit the number of retries to 15 (:phab:`T165898`)

3.0.20170403
------------

*3 April 2017*

* First major release from master branch
* requests package is mandatory
* Deprecate previous 2.0 branches and tags

Bugfixes
^^^^^^^^
* Use default summary when summary value does not contain a string (:phab:`T160823`)
* Enable specialbots.py for PY3 (:phab:`T161457`)
* Change tw(n)translate from Site.code to Site.lang dependency (:phab:`T140624`)
* Do not use the "imp" module in Python 3 (:phab:`T158640`)
* Make sure the order of parameters does not change (:phab:`T161291`)
* Use pywikibot.tools.Counter instead of collections.Counter (:phab:`T160620`)
* Introduce a new site method page_from_repository()
* Add pagelist tag for replaceExcept (:phab:`T151940`)
* logging in python3 when deprecated_args decorator is used (:phab:`T159077`)
* Avoid ResourceWarning using subprocess in python 3.6 (:phab:`T159646`)
* load_pages_from_pageids: do not fail on empty string (:phab:`T153592`)
* Add missing not-equal comparison for wbtypes (:phab:`T158848`)
* textlib.getCategoryLinks catch invalid category title exceptions (:phab:`T154309`)
* Fix html2unicode (:phab:`T130925`)
* Ignore first letter case on 'first-letter' sites, obey it otherwise (:phab:`T130917`)
* textlib.py: Limit catastrophic backtracking in FILE_LINK_REGEX (:phab:`T148959`)
* FilePage.get_file_history(): Check for len(self._file_revisions) (:phab:`T155740`)
* Fix for positional_arg behavior of GeneratorFactory (:phab:`T155227`)
* Fix broken LDAP based login (:phab:`T90149`)

Improvements
^^^^^^^^^^^^
* Simplify User class
* Renamed isImage and isCategory
* Add -property option to pagegenerators.py
* Add a new site method pages_with_property
* Allow retrieval of unit as ItemPage for WbQuantity (:phab:`T143594`)
* return result of userPut with put_current method
* Provide a new generator which yields a subclass of Page
* Implement FilePage.download()
* make general function to compute file sha
* Support adding units to WbQuantity through ItemPage or entity url (:phab:`T143594`)
* Make PropertyPage.get() return a dictionary
* Add Wikibase Client extension requirement to APISite.unconnectedpages()
* Make Wikibase Property provide labels data
* APISite.data_repository(): handle warning with re.match() (:phab:`T156596`)
* GeneratorFactory: make getCategory respect self.site (:phab:`T155687`)
* Fix and improve default regexes

Updates
^^^^^^^
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
* Add 'Bilde' as a namespace alias for file namespace of nn Wikipedia (:phab:`T154947`)

2.0rc5
------

*17 August 2016*

* Last stable 2.0 branch

Bugfixes
^^^^^^^^
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
^^^^^^^^
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
^^^^^^^^
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
^^^^^^^^^^^^^^^^^^^^^
* Changing the sandbox content template on Fa WP

Family file updates
^^^^^^^^^^^^^^^^^^^
* Remove broken wikis from battlestarwiki family
* Adding euskara and sicilianu languages to Vikidia family
* WOW Wiki subdomains hr, ro & sr deleted
* Add new Wikipedia languages gom and lrc

Bugfixes
^^^^^^^^
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
* AppVeyor CI Win32 builds
* New scripts patrol.py and piper.py ported from old compat branch
* Bugfixes and improvements
* Localisation updates

2.0b3
-----

*30 November 2014*

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

*19 June 2007*

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
