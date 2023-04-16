Scripts Changelog
=================

8.1.0
-----

archivebot
~~~~~~~~~~

* Processing speed was improved and is up to 20 times faster, 2-3 times on average

redirect
~~~~~~~~

* Use ``Bot:`` prefixed summary (:phab:`T161459`)
* Fix ``-namespace`` usage if RedirectGenerator is used (:phab:`T331243`)


8.0.2
-----

clean_sandbox
~~~~~~~~~~~~~

* L10N for es-wikis

8.0.1
-----

clean_sandbox
~~~~~~~~~~~~~

* L10N for several wikis

touch
~~~~~

* Login first when starting the script (:phab:`T328204`)


8.0.0
-----

blockpageschecker
~~~~~~~~~~~~~~~~~

* Fix neutral additive element

category
~~~~~~~~

* Enable pagegenerators options with ``move`` and ``remove`` actions (:phab:`T318239`)

category_graph
~~~~~~~~~~~~~~

* :mod:`category_graph` script was added which creates category graph in formats dot, svg and html5

clean_sandbox
~~~~~~~~~~~~~

* L10N updates
* A `-textfile` option was addet to fetch the text from a file

create_isbn_edition
~~~~~~~~~~~~~~~~~~~

* Fix argument parsing

fixing_redirects
~~~~~~~~~~~~~~~~

* Skip invalid link titles (:phab:`T324434`)

interwiki
~~~~~~~~~

Fix string concatenation (:phab:`T322180`)

touch
~~~~~

Provide bulk purge to run upto 1000 times faster


7.7.0
-----

archivebot
~~~~~~~~~~

* Process pages in parallel tasks with ``-async`` option (:phab:`T57899`)
* Add -sort option to sort archives by (latest) timestamp
* Archive unsigned threads using timestamp of the next thread (:phab:`T69663`, :phab:`T182685`)

category_redirect
~~~~~~~~~~~~~~~~~

* Use localized template prefix (:phab:`T318049`)

create_isbn_edition
~~~~~~~~~~~~~~~~~~~

* New script to load ISBN related data into Wikidata (:phab:`T314942`)

watchlist
~~~~~~~~~

* Watchlist is retrieved faster in parallel tasks (:phab:`T57899`)
* Enable watchlist.refresh_all for API generator access (:phab:`T316359`)

7.6.0
-----

*21 August 2022*

archivebot
~~~~~~~~~~

* Use ``User:MiszaBot/config`` as default template
* Raise MalformedConfigError if 'maxarchivesize' is 0 (:phab:`T313886`)
* Preserve thread order in archive even if threads are archived later (:phab:`T312773`, :phab:`T314560`)
* Skip the page if it does not exist
* Fix for DiscussionPage.size() (:phab:`T313886`)
* Decrease memory usage and improve processing speed

interwiki
~~~~~~~~~

* Fix wrong Subject property

pagefromfile
~~~~~~~~~~~~

* Derive PageFromFileReader from tools.collections.GeneratorWrapper

7.5.2
-----

*26 July 2022*

archivebot
~~~~~~~~~~

* Add localized "archive" variables  (:phab:`T71551`, :phab:`T313682`, :phab:`T313692`)

7.5.1
-----

*24 July 2022*

archivebot
~~~~~~~~~~

* Replace archive pattern fields to string conversion (:phab:`T313692`)

7.5.0
-----

*22 July 2022*

harvest_template
~~~~~~~~~~~~~~~~

*  Support harvesting time values (:phab:`T66503`)
*  Do not rely on self.current_page.site
*  Add ``-inverse`` option for inverse claims (:phab:`T173238`)
*  Only follow redirects in harvest_template.py if no wikibase item
   exists (:phab:`T311883`)

7.4.0
-----

*26 June 2022*

addtext
~~~~~~~

*  Fix for -createonly option (:phab:`T311173`)

harvest_template
~~~~~~~~~~~~~~~~

*  Add -confirm option which sets ‘always’ option to False
   (:phab:`T310356`)
*  Do not show a warning if generator is specified later
   (:phab:`T310418`)

interwiki
~~~~~~~~~

*  Fix regression where interwiki script removes all interwiki links
   (:phab:`T310964`)
*  Assign compareLanguages to be reused and fix process_limit_two call
   (:phab:`T310908`)

listpages
~~~~~~~~~

*  Print the page list immediately except pages are preloaded

nowcommons
~~~~~~~~~~

*  Use treat_page method (:phab:`T309456`)
*  Fix several bugs (:phab:`T309473`)

7.3.0
-----

*21 May 2022*

general
~~~~~~~

*  Call ExistingPageBot.skip_page() first (:phab:`T86491`)

delete
~~~~~~

*  Count deleted pages and other actions (:phab:`T212040`)

replace
~~~~~~~

*  A -nopreload option was added

weblinkchecker
~~~~~~~~~~~~~~

*  Throttle connections to the same host (:phab:`T152350`)
*  Do not kill threads after generator is exhausted (:phab:`T113139`)
*  Use Page.extlinks() to get external links (:phab:`T60812`)

update_script
~~~~~~~~~~~~~

*  update_script script was removed

7.2.1
-----

*07 May 2022*

movepages
~~~~~~~~~

*  Fix regression of option parsing (:phab:`T307826`)

7.2.0
-----

*26 April 2022*

general
~~~~~~~

*  Archived scripts were removed

archive
~~~~~~~

*  Fix trailing newlines (:phab:`T306529`)

checkimages
~~~~~~~~~~~

*  Use page_from_repository() method to read categoried from wikibase
*  Use ``itertools.zip_longest`` to find the most important image

dataextend
~~~~~~~~~~

*  A -showonly option was added to only show claims of an ItemPage
*  This new script was added. It is able to add properties, identifiers
   and sources to WikiBase items

delinker
~~~~~~~~

*  New delinker script was added; it replaces compat’s CommonsDelinker
   (:phab:`T299563`)

image
~~~~~

*  Fix image regex (:phab:`T305226`, :phab:`T305227`)

reflinks
~~~~~~~~

*  Ignore Bloomberg captcha (:phab:`T306304`)
*  Fix cp encodings (:phab:`T304830`)

replace
~~~~~~~

*  A -quiet option was added to omit message when no change was made

7.1.1
-----

*15 April 2022*

replace
~~~~~~~

*  Fix regression of XmlDumpPageGenerator

7.1.0
-----

*26 March 2022*

fixing_redirects
~~~~~~~~~~~~~~~~

*  -always option was enabled

reflinks
~~~~~~~~

*  Solve UnicodeDecodeError in ReferencesRobot.treat()
   (:phab:`T304288`)
*  Decode pdfinfo if it is bytes content (:phab:`T303731`)

7.0.0
-----

*26 February 2022*

general
~~~~~~~

*  L10N updates
*  Provide ConfigParserBot for several scripts (:phab:`T223778`)

add_text
~~~~~~~~

*  Provide -create and -createonly options (:phab:`T291354`)
*  Deprecated function get_text() was removed in favour of Page.text and
   BaseBot.skip_page()
*  Deprecated function put_text() was removed in favour of
   BaseBot.userPut() method
*  Deprecated function add_text() were remove in favour of
   textlib.add_text()

blockpageschecker
~~~~~~~~~~~~~~~~~

*  Use different edit comments when adding, changeing or removing
   templates (:phab:`T291345`)
*  Derive CheckerBot from ConfigParserBot (:phab:`T57106`)
*  Derive CheckerBot from CurrentPageBot (:phab:`T196851`,
   :phab:`T171713`)

category
~~~~~~~~

*  CleanBot was added which can be invoked by clean action option
*  Recurse CategoryListifyRobot with depth
*  Show a warning if a pagegenerator option is not enabled
   (:phab:`T298522`)
*  Deprecated code parts were removed

checkimages
~~~~~~~~~~~

*  Skip PageSaveRelatedError and ServerError when putting talk page
   (:phab:`T302174`)

commonscat
~~~~~~~~~~

*  Ignore InvalidTitleError in CommonscatBot.findCommonscatLink
   (:phab:`T291783`)

cosmetic_changes
~~~~~~~~~~~~~~~~

*  Ignore InvalidTitleError in CosmeticChangesBot.treat_page
   (:phab:`T293612`)

djvutext
~~~~~~~~

*  pass site arg only once (:phab:`T292367`)

fixing_redirects
~~~~~~~~~~~~~~~~

*  Let only put_current show the message “No changes were needed”
*  Use concurrent.futures to retrieve redirect or moved targets
   (:phab:`T298789`)
*  Add an option to ignore solving moved targets (:phab:`T298789`)

imagetransfer
~~~~~~~~~~~~~

*  Add support for chunked uploading (:phab:`T300531`)

newitem
~~~~~~~

*  Do not pass OtherPageSaveRelatedError silently

pagefromfile
~~~~~~~~~~~~

*  Preload pages instead of reading them one by one before putting
   changes
*  Don’t ask for confirmation by default (:phab:`T291757`)

redirect
~~~~~~~~

*  Use site.maxlimit to determine the highest limit to load
   (:phab:`T299859`)

replace
~~~~~~~

*  Enable default behaviour with -mysqlquery (:phab:`T299306`)
*  Deprecated “acceptall” and “addedCat” parameters were replaced by
   “always” and “addcat”

revertbot
~~~~~~~~~

*  Add support for translated dates/times (:phab:`T102174`)
*  Deprecated “max” parameter was replaced by “total”

solve_disambiguation
~~~~~~~~~~~~~~~~~~~~

*  Remove deprecated properties in favour of DisambiguationRobot.opt
   options

touch
~~~~~

\*Do not pass OtherPageSaveRelatedError silently

unusedfiles
~~~~~~~~~~~

*  Use oldest_file_info.user as uploader (:phab:`T301768`)

6.6.1
-----

*21 September 2021*

category
~~~~~~~~

*  Fix -match option

6.6.0
-----

*15 September 2021*

add_text
~~~~~~~~

*  Add -major flag to disable minor edit flag when saving

6.5.0
-----

*05 August 2021*

reflinks
~~~~~~~~

*  Don’t ignore identical references with newline in ref content
   (:phab:`T286369`)
*  L10N updates

6.4.0
-----

*01 July 2021*

general
~~~~~~~

*  show a warning if pywikibot.__version_\_ is behind
   scripts.__version_\_

addtext
~~~~~~~

*  Deprecate get_text, put_text and add_text functions
   (:phab:`T284388`)
*  Use AutomaticTWSummaryBot and NoRedirectPageBot bot class instead of
   functions (:phab:`T196851`)

blockpageschecker
~~~~~~~~~~~~~~~~~

*  Script was unarchived

commonscat
~~~~~~~~~~

*  Enable multiple sites (:phab:`T57083`)
*  Use new textlib.add_text function

cosmetic_changes
~~~~~~~~~~~~~~~~

*  set -ignore option to CANCEL.MATCH by default (:phab:`T108446`)

fixing_redirects
~~~~~~~~~~~~~~~~

*  Add -overwrite option (:phab:`T235219`)

imagetransfer
~~~~~~~~~~~~~

*  Skip pages which does not exist on source site (:phab:`T284414`)
*  Use roundrobin_generators to combine multiple template inclusions
*  Allow images existing in the shared repo (:phab:`T267535`)

template
~~~~~~~~

*  Do not try to initialze generator twice in TemplateRobot
   (:phab:`T284534`)

update_script
~~~~~~~~~~~~~

*  compat2core script was restored and renamed to update_script

version
~~~~~~~

*  Show all mandatory dependecies

6.3.0
-----

*31 May 2021*

addtext
~~~~~~~

*  -except option was removed in favour of commonly used -grepnot

archivebot
~~~~~~~~~~

*  Durations must to have a time unit

6.2.0
-----

*28 May 2021*

general
~~~~~~~

*  image.py was restored
*  nowcommons.py was restored
*  i18n updates
*  L10N updates

category
~~~~~~~~

*  dry parameter of CategoryAddBot will be removed

commonscat
~~~~~~~~~~

*  Ignore InvalidTitleError (:phab:`T267742`)
*  exit checkCommonscatLink method if target name is empty
   (:phab:`T282693`)

fixing_redirects
~~~~~~~~~~~~~~~~

*  ValueError will be ignored (:phab:`T283403`, :phab:`T111513`)
*  InterwikiRedirectPageError will be ignored (:phab:`T137754`)
*  InvalidPageError will be ignored (:phab:`T280043`)

reflinks
~~~~~~~~

*  Use consecutive reference numbers for autogenerated links

replace
~~~~~~~

*  InvalidPageError will be ignored (:phab:`T280043`)

upload
~~~~~~

*  Support async chunked uploads (:phab:`T129216`)

6.1.0
-----

*17 April 2021*

general
~~~~~~~

*  commonscat.py was restored
*  compat2core.py script was archived
*  djvutext.py was restored
*  interwiki.py was restored
*  patrol.py was restored
*  watchlist.py was restored

archivebot
~~~~~~~~~~

*  PageArchiver.maxsize must be defined before load_config()
   (:phab:`T277547`)
*  Time period must have a qualifier

imagetransfer
~~~~~~~~~~~~~

*  Fix usage of -tofamily -tolang options (:phab:`T279232`)

misspelling
~~~~~~~~~~~

*  Use the new DisambiguationRobot interface and options

reflinks
~~~~~~~~

*  Catch urllib3.LocationParseError and skip link (:phab:`T280356`)
*  L10N updates
*  Avoid dupliate reference names (:phab:`T278040`)

solve_disambiguation
~~~~~~~~~~~~~~~~~~~~

*  Keyword arguments are recommended if deriving the bot; opt option
   handler is used.

welcome
~~~~~~~

*  Fix reporting bad account names

6.0.0
-----

*15 March 2021*

general
~~~~~~~

*  interwikidumps.py, cfd.py and featured.py scripts were deleted
   (:phab:`T223826`)
*  Long time unused scripts were archived (:phab:`T223826`). Ask to
   recover if needed.
*  pagegenerators.handle_args() is used in several scripts

archivebot
~~~~~~~~~~

*  Always take ‘maxarticlesize’ into account when saving
   (:phab:`T276937`)
*  Remove deprecated parts

category
~~~~~~~~

*  add ‘namespaces’ option to category ‘listify’

commons_information
~~~~~~~~~~~~~~~~~~~

*  New script to wrap Commons file descriptions in language templates

generate_family_file
~~~~~~~~~~~~~~~~~~~~

*  Ignore ssl certificate validation (:phab:`T265210`)

login
~~~~~

*  update help string

maintenance
~~~~~~~~~~~

*  Add a preload_sites.py script to preload site informations
   (:phab:`T226157`)

reflinks
~~~~~~~~

*  Force pdf file to be closed (:phab:`T276747`)
*  Fix http.fetch response data attribute
*  Fix treat process flow

replace
~~~~~~~

*  Add replacement description to -summary message

replicate_wiki
~~~~~~~~~~~~~~

*  replace pages in all sites (:phab:`T275291`)

solve_disambiguation
~~~~~~~~~~~~~~~~~~~~

*  Deprecated methods were removed
*  Positional arguments of DisambiguationRobot are deprecated, also some
   keywords were replaced

unusedfiles
~~~~~~~~~~~

*  Update unusedfiles.py to add custom templates

5.6.0
-----

*24 January 2021*

general
~~~~~~~

*  pagegenerators handleArg was renamed to handle_arg
   (:phab:`T271437`)
*  i18n updates

add_text
~~~~~~~~

*  bugfix: str.join() expects an iterable not multiple args
   (:phab:`T272223`)

redirect
~~~~~~~~

*  pagegenerators -page option was implemented (:phab:`T100643`)
*  pagegenerators namespace filter was implemented (:phab:`T234133`,
   :phab:`T271116`)

weblinkchecker
--------------

*  Deprecated LinkChecker class was removed

5.5.0
-----

\*12 January 2021

general
~~~~~~~

*  i18n updates
*  L10N updates

add_text
~~~~~~~~

*  -except option was renamed to -grepnot from pagegenerators

solve_disambiguation
~~~~~~~~~~~~~~~~~~~~

*  ignore ValueError when parsing a Link object (:phab:`T111513`)

5.4.0
-----

*2 January 2021*

general
~~~~~~~

*  i18n updates

replace
~~~~~~~

*  Desupported ReplaceRobot.doReplacements method was removed

5.3.0
-----

*19 December 2020*

data_ingestion
~~~~~~~~~~~~~~

*  Remove deprecated Photo.reader property and Photo.doSingle() method

replicate_wiki
~~~~~~~~~~~~~~

*  Remove deprecated namespace function

template
~~~~~~~~

*  remove deprecated XmlDumpTemplatePageGenerator

5.2.0
-----

*10 December 2020*

general
~~~~~~~

*  Removed unsupported BadTitle Exception (:phab:`T267768`)
*  Replaced PageNotSaved by PageSaveRelatedError (:phab:`T267821`)
*  Update scripts to support Python 3.5+ only
*  i18n updates
*  L10N updates

basic
~~~~~

*  Make BasicBot example a ConfigParserBot to explain the usage

clean_sandbox
~~~~~~~~~~~~~

*  Fix TypeError (:phab:`T267717`)

fixing_redirects
~~~~~~~~~~~~~~~~

*  Ignore RuntimeError for missing ‘redirects’ in api response
   (:phab:`T267567`)

imagetransfer
~~~~~~~~~~~~~

*  Implement -tosite command and other improvements
*  Do not use UploadRobot.run() with imagetransfer (:phab:`T267579`)

interwiki
~~~~~~~~~

*  Use textfile for interwiki dumps and enable -restore:all option
   (:phab:`T74943`, :phab:`T213624`)

makecat
~~~~~~~

*  Use input_choice for options
*  New option handling
*  Other improvements

revertbot
~~~~~~~~~

*  Take rollbacktoken to revert (:phab:`T250509`)

solve_disambiguation
~~~~~~~~~~~~~~~~~~~~

*  Write ignoring pages as a whole

touch
~~~~~

*  Fix available_options and purge options (:phab:`T268394`)

weblinkchecker
~~~~~~~~~~~~~~

*  Fix AttributeError of HttpRequest (:phab:`T269821`)

5.1.0
-----

*1 November 2020*

general
~~~~~~~

*  i18n updates
*  switch to new OptionHandler interface (:phab:`T264721`)

change_pagelang
~~~~~~~~~~~~~~~

*  New script was added

download_dump
~~~~~~~~~~~~~

*  Make ``dumpdate`` param work when using the script in Toolforge
   (:phab:`T266630`)

imagetransfer
~~~~~~~~~~~~~

*  Remove outdated “followRedirects” parameter from imagelinks(); treat
   instead of run method (:phab:`T266867`, :phab:`T196851`,
   :phab:`T171713`)

interwiki
~~~~~~~~~

*  Replace deprecated originPage by origin in Subjects

misspelling
~~~~~~~~~~~

*  Enable misspelling.py for several sites using wikidata
   (:phab:`T258859`, :phab:`T94681`)

noreferences
~~~~~~~~~~~~

*  Rename NoReferencesBot.run to treat (:phab:`T196851`,
   :phab:`T171713`)
*  Use wikidata item instead of dropped MediaWiki message for default
   category (:phab:`T266413`)

reflinks
~~~~~~~~

*  Derive ReferencesRobot from ExistingPageBot and NoRedirectPageBot
*  Use chardet to find a valid encoding (266862)
*  Rename ReferencesRobot.run to treat (:phab:`T196851`,
   :phab:`T171713`)
*  Ignore duplication replacements inside templates (:phab:`T266411`)
*  Fix edit summary (:phab:`T265968`)
*  Add Server414Error in and close file after reading
   (:phab:`T266000`)
*  Call ReferencesRobot.setup() (:phab:`T265928`)

welcome
~~~~~~~

*  Replace \_COLORS and \_MSGS dicts by Enum

5.0.0
-----

*19 October 2020*

general
~~~~~~~

*  i18n updates
*  L10N updates
*  Remove deprecated use of fileUrl
*  Remove ArgumentDeprecationWarning for several scripts

casechecker
~~~~~~~~~~~

*  Split initializer and put getting whitelist to its own method

checkimages
~~~~~~~~~~~

*  Re-enable -sleep parameter (:phab:`T264521`)

commonscat
~~~~~~~~~~

*  get commons category from wikibase (:phab:`T175207`)
*  Adjust save counter (:phab:`T262772`)

flickrripper
~~~~~~~~~~~~

*  Improve option handling

imagecopy_self
~~~~~~~~~~~~~~

*  Improvements were made

imagetransfer
~~~~~~~~~~~~~

*  Do not encode str to bytes (:phab:`T265257`)

match_images
~~~~~~~~~~~~

*  Improvements

parser_function_count
~~~~~~~~~~~~~~~~~~~~~

Porting parser_function_count.py from compat to core/scripts
(:phab:`T66878`)

reflinks
~~~~~~~~

decode byte-like object meta_content.group() (:phab:`T264575`)

speedy_delete
~~~~~~~~~~~~~

*  port speedy_delete.py to core (:phab:`T66880`)

weblinkchecker
~~~~~~~~~~~~~~

*  Use ThreadList with weblinkchecker

maintenance
~~~~~~~~~~~

*  new maintenance script sorting_order was added
*  new maintenance script update_linktrails was added

4.3.0
-----

*2 September 2020*

general
~~~~~~~

*  i18n updates

4.2.0
-----

*28 August 2020*

general
~~~~~~~

*  i18n updates

archivebot
~~~~~~~~~~

*  Determine whether counter matters only once

4.1.1
-----

*18 August 2020*

general
~~~~~~~

*  Add missing commas in string contants

4.1.0
-----

*16 August 2020*

general
~~~~~~~

*  i18n updates

download_dump
~~~~~~~~~~~~~

*  Move this script to script folder (:phab:`T123885`,
   :phab:`T184033`)

replace
-------

*  Show a FutureWarning for deprecated doReplacements method

replicate_wiki
--------------

*  Show a FutureWarning for deprecated namespace function

template
--------

*  Show a FutureWarning for deprecated XmlDumpTemplatePageGenerator
   class

4.0.0
-----

*4 August 2020*

general
~~~~~~~

*  Remove Python 2 related code (:phab:`T257399`)
*  i18n updates
*  L10N updates

archivebot
~~~~~~~~~~

*  Only mention archives where something was really archived
*  Reset counter when “era” changes (:phab:`T215247`)
*  Code improvements and cleanups
*  Fix ShouldArchive type
*  Refactor PageArchiver’s main loop
*  Move archiving logic to PageArchiver
*  Fix str2size to allow space separators

cfd
~~~

*  Script was archived and is no longer supported (:phab:`T223826`)

delete
~~~~~~

*  Use Dict in place of DefaultDict (:phab:`T257770`)
