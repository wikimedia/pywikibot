Current release changes
~~~~~~~~~~~~~~~~~~~~~~~

Breaking changes
^^^^^^^^^^^^^^^^

* interwiki_graph module was removed (T223826)
* Require setuptools >= 20.2 due to PEP 440
* Support of MediaWiki < 1.23 has been dropped (T268979)
* APISite.loadimageinfo will no longer return any content
* Return requests.Response with http.request() instead of plain text (T265206)
* config.db_hostname has been renamed to db_hostname_format

Code cleanups
^^^^^^^^^^^^^

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
^^^^^^^^^^^^^

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
* Fix date.formats['MonthName'] behaviour  (T273573)
* Implement pagegenerators.handle_args() to process all options at once
* Add enabled_options, disabled_options to GeneratorFactory (T271320)
* Move interwiki() interwiki_prefix() and local_interwiki() methods from BaseSite to APISite
* Add requests.Response.headers to log when an API error occurs (T272325)

Future release notes
~~~~~~~~~~~~~~~~~~~~

* 6.0.0: User.name() method will be removed in favour of User.username property
* 5.6.0: pagenenerators.handleArg() method will be removed in favour of handle_arg() (T271437)
* 5.5.0: Site.getuserinfo() method will be dropped in favour of userinfo property
* 5.5.0: Site.getglobaluserinfo() method will be dropped in favour of globaluserinfo property
* 5.0.0: OptionHandler.options dict will be removed in favour of OptionHandler.opt
* 5.0.0: Methods deprecated for 5 years or longer will be removed
* 5.0.0: pagegenerators.ReferringPageGenerator is desupported and will be removed
