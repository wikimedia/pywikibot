# Schripts Changelog

## 5.2.0
*10 December 2020*

### general
* Removed unsupported BadTitle Exception (T267768)
* Replaced PageNotSaved by PageSaveRelatedError (T267821)
* Update scripts to support Python 3.5+ only
* i18n updates
* L10N updates

### basic
* Make BasicBot example a ConfigParserBot to explain the usage

### clean_sandbox
* Fix TypeError (T267717)

### fixing_redirects
*  Ignore RuntimeError for missing 'redirects' in api response (T267567)

### imagetransfer
* Implement -tosite command and other improvements
* Do not use UploadRobot.run() with imagetransfer (T267579)

### interwiki
* Use textfile for interwiki dumps and enable -restore:all option (T74943, T213624)

### makecat
* Use input_choice for options
* New option handling
* Other improvements

### revertbot
* Take rollbacktoken to revert (T250509)

### solve_disambiguation
* Write ignoring pages as a whole

### touch
* Fix available_options and purge options (T268394)

### weblinkchecker
* Fix AttributeError of HttpRequest (T269821)


## 5.1.0
*1 November 2020*

### general
* i18n updates
* switch to new OptionHandler interface (T264721)

### change_pagelang
* New script was added

### download_dump
*  Make `dumpdate` param work when using the script in Toolforge (T266630)

### imagetransfer
* Remove outdated "followRedirects" parameter from imagelinks(); treat instead of run method (T266867, T196851, T171713)

### interwiki
* Replace deprecated originPage by origin in Subjects

### misspelling
* Enable misspelling.py for several sites using wikidata (T258859, T94681)

### noreferences
* Rename NoReferencesBot.run to treat (T196851, T171713)
* Use wikidata item instead of dropped MediaWiki message for default categoy (T266413)

### reflinks
* Derive ReferencesRobot from ExistingPageBot and NoRedirectPageBot
* Use chardet to find a valid encoding (266862)
* Rename ReferencesRobot.run to treat (T196851, T171713)
* Ignore duplication replacements inside templates (T266411)
* Fix edit summary (T265968)
* Add Server414Error in and close file after reading (T266000)
* Call ReferencesRobot.setup() (T265928)

### welcome
* Replace _COLORS and _MSGS dicts by Enum


## 5.0.0
*19 October 2020*

### general
* i18n updates
* L10N updates
* Remove deprecated use of fileUrl
* Remove ArgumentDeprecationWarning for several scripts

### casechecker
*  Split initializer and put getting whitelist to its own method

### checkimages
* Re-enable -sleep parameter (T264521)

### commonscat
* get commons categoy from wikibase (T175207)
* Adjust save counter (T262772)

### flickrripper
* Improve option handling

### imagecopy_self
* Improvements were made

### imagetransfer
* Do not encode str to bytes (T265257)

### match_images
* Improvements

### parser_function_count
Porting parser_function_count.py from compat to core/scripts (T66878)

### reflinks
decode byte-like object meta_content.group() (T264575)

### speedy_delete
* port speedy_delete.py to core (T66880)

### weblinkchecker
* Use ThreadList with weblinkchecker

### maintenance
* new maintenance script sorting_order was added
* new maintenance script update_linktrails was added


## 4.3.0
*2 September 2020*

### general
* i18n updates


## 4.2.0
*28 August 2020*

### general
* i18n updates

### archivebot
* Determine whether counter matters only once


## 4.1.1
*18 August 2020*

### general
* Add missing commas in string contants


## 4.1.0
*16 August 2020*

### general
* i18n updates

### download_dump
* Move this script to script folder (T123885, T184033)

## replace
* Show a FutureWarning for deprecated doReplacements method

## replicate_wiki
* Show a FutureWarning for deprecated namespace function

## template
* Show a FutureWarning for deprecated XmlDumpTemplatePageGenerator class


## 4.0.0
*4 August 2020*

### general
* Remove Python 2 related code (T257399)
* i18n updates
* L10N updates

### archivebot
* Only mention archives where something was really archived
* Reset counter when "era" changes (T215247)
* Code improvements and cleanups
* Fix ShouldArchive type
* Refactor PageArchiver's main loop
* Move archiving logic to PageArchiver
* Fix str2size to allow space separators

### cfd
* Script was archived and is no longer supported (T223826)

### delete
*  Use Dict in place of DefaultDict (T257770)
