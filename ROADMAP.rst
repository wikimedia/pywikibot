Current release
~~~~~~~~~~~~~~~

  **Note: This is the last release supporting Python 2 and Python 3.4**

* Wait in BaseBot.exit() until asynchronous saving pages are completed
* Solve IndexError when showing an empty diff with a non-zero context (T252724)
* linktrails were added or updated for a lot of sites
* Resolve namespaces with underlines (T252940)
* Fix getversion_svn for Python 3.6+ (T253617, T132292)
* Bugfixes and improvements
* Localisation updates

Future releases
~~~~~~~~~~~~~~~

* (current) tools.count, tools.Counter, tools.OrderedDict and ContextManagerWrapper will be removed
* (current) getFilesFromAnHash and getImagesFromAnHash Site methods will be removed
* 3.0.20200508: PageNotFound, SpamfilterError and UserActionRefuse exceptions will be removed (T253681)
* 3.0.20200508: Page.getVersionHistory and Page.fullVersionHistory() methods will be removed (T136513, T151110)
* 3.0.20200405: Site and Page methods deprecated for 10 years or longer will be removed
* 3.0.20200326: Functions dealing with stars list will be removed
* 3.0.20200306: Support of MediaWiki releases below 1.19 will be dropped (T245350)
* 3.0.20200306: tools.ip will be dropped in favour of tools.is_IP (T243171)
* 3.0.20200111: Support for Python 3.4 will be dropped shortly (T239542)
* 3.0.20190722: Support for Python 2 will be dropped shortly (T213287)
