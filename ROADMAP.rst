Current release changes
~~~~~~~~~~~~~~~~~~~~~~~

* Move latest revision id handling to WikibaseEntity (T233406)
* Load wikibase entities when necessary (T245809)
* Fix path for stable release in version.getversion() (T262558)
* "since" parameter in EventStreams given as Timestamp or MediaWiki timestamp string has been fixed
* Some methods deprecated for 6 years or longer were removed
* Page.getVersionHistory and Page.fullVersionHistory() methods were removed (T136513, T151110)
* Allow multiple types of contributors parameter given for Page.revision_count()
* Deprecated tools.UnicodeMixin and tools.IteratorNextMixin has been removed
* Localisation updates


Future release notes
~~~~~~~~~~~~~~~~~~~~

* 4.3.0: Unsused UserBlocked exception will be removed
* 4.3.0: Deprecated Page.contributingUsers() will be removed
* 4.2.0: tools.StringTypes will be removed
* 4.1.0: Deprecated editor.command will be removed
* 4.1.0: tools.open_compressed, tools.UnicodeType and tools.signature will be removed
* 4.1.0: comms.PywikibotCookieJar and comms.mode_check_decorator will be removed
* 4.0.0: Unused parameters of page methods like forceReload, insite, throttle, step will be removed
* 4.0.0: Methods deprecated for 6 years or longer will be removed
* 3.0.20200306: Support of MediaWiki releases below 1.19 will be dropped (T245350)
