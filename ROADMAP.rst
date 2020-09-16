Current release changes
~~~~~~~~~~~~~~~~~~~~~~~

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

* 4.4.0: Property.getTspe() method will be removed
* 4.4.0: Request.http_params() method will be removed
* 4.4.0: DataSite.get_item() method will be removed
* 4.4.0: date.MakeParameter() function will be removed
* 4.4.0: pagegenerators.ReferringPageGenerator is desupported and will be removed
* 4.3.0: Unsused UserBlocked exception will be removed
* 4.3.0: Deprecated Page.contributingUsers() will be removed
* 4.2.0: tools.StringTypes will be removed
* 4.1.0: Deprecated editor.command will be removed
* 4.1.0: tools.open_compressed, tools.UnicodeType and tools.signature will be removed
* 4.1.0: comms.PywikibotCookieJar and comms.mode_check_decorator will be removed
* 4.0.0: Unused parameters of page methods like forceReload, insite, throttle, step will be removed
