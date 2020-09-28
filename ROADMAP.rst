Current release changes
~~~~~~~~~~~~~~~~~~~~~~~

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


Future release notes
~~~~~~~~~~~~~~~~~~~~

* 5.0.0: version.getfileversion() is desupported and will be removed
* 5.0.0: Methods deprecated for 5 years or longer will be removed
* 5.0.0: Outdated recentchanges parameter will be removed
* 5.0.0: site.LoginStatus will be removed in favour of login.LoginStatus
* 5.0.0: Property.getType() method will be removed
* 5.0.0: Request.http_params() method will be removed
* 5.0.0: DataSite.get_item() method will be removed
* 5.0.0: date.MakeParameter() function will be removed
* 5.0.0: pagegenerators.ReferringPageGenerator is desupported and will be removed
* 4.3.0: Unsused UserBlocked exception will be removed
* 4.3.0: Deprecated Page.contributingUsers() will be removed
* 4.2.0: tools.StringTypes will be removed
* 4.1.0: Deprecated editor.command will be removed
* 4.1.0: tools.open_compressed, tools.UnicodeType and tools.signature will be removed
* 4.1.0: comms.PywikibotCookieJar and comms.mode_check_decorator will be removed
