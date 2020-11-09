Current release changes
~~~~~~~~~~~~~~~~~~~~~~~

* Fix get_known_families() for wikipedia_family (T267196)
* Move _InterwikiMap class to site/_interwikimap.py
* instantiate a CosmeticChangesToolkit by passing a page
* Create a Site from sitename
* pywikibot.Site() parameters "interface" and "url" must be keyworded
* Lookup the code parameter in xdict first (T255917)
* Remove interwiki_forwarded_from list from family files (T104125)
* Rewrite Revision class; each data can be accessed either by key or as an attribute (T102735, T259428)
* L10N-Updates


Future release notes
~~~~~~~~~~~~~~~~~~~~

* 5.1.0: Positional arguments of page.Revision must be replaced by keyword arguments (T259428)
* 5.0.0: wikistats methods fetch, raw_cached, csv, xml will be removed
* 5.0.0: PageRelatedError.getPage() will be removes in favour of PageRelatedError.page
* 5.0.0: HttpRequest result of http.fetch() will be replaced by requests.Response (T265206)
* 5.0.0: edit, move, create, upload, unprotect and prompt parameters of Page.protect() will be removed (T227610)
* 5.0.0: OptionHandler.options dict will be removed in favour of OptionHandler.opt
* 5.0.0: version.getfileversion() is desupported and will be removed
* 5.0.0: Methods deprecated for 5 years or longer will be removed
* 5.0.0: Outdated recentchanges parameter will be removed
* 5.0.0: site.LoginStatus will be removed in favour of login.LoginStatus
* 5.0.0: Property.getType() method will be removed
* 5.0.0: Request.http_params() method will be removed
* 5.0.0: DataSite.get_item() method will be removed
* 5.0.0: date.MakeParameter() function will be removed
* 5.0.0: pagegenerators.ReferringPageGenerator is desupported and will be removed
* 4.3.0: Unused UserBlocked exception will be removed
* 4.3.0: Deprecated Page.contributingUsers() will be removed
