Current release changes
~~~~~~~~~~~~~~~~~~~~~~~

* Remove deprecated args for Page.protect() (T227610)
* Move BaseSite its own site/_basesite.py file
* Improve toJSON() methods in page.__init__.py
* _is_wikibase_error_retryable rewritten (T48535, 268645)
* Replace FrozenDict with frozenmap
* WikiStats table may be sorted by any key
* Retrieve month names from mediawiki_messages when required
* Move Namespace and NamespacesDict to site/_namespace.py file
* Fix TypeError in api.LoginManager (T268445)
* Add repr() method to BaseDataDict and ClaimCollection
* Define availableOptions as deprecated property
* Do not strip all whitespaces from Link.title (T197642)
* Introduce a common BaseDataDict as parent for LanguageDict and AliasesDict
* Replaced PageNotSaved by PageSaveRelatedError (T267821)
* Add -site option as -family -lang shortcut
* Enable APISite.exturlusage() with default parameters (T266989)
* Update tools._unidata._category_cf from Unicode version 13.0.0
* Move TokenWallet to site/_tokenwallet.py file
* Fix import of httplib after release of requests 2.25 (T267762)
* user keyword parameter can be passed to Site.rollbackpage() (T106646)
* Check for {{bots}}/{{nobots}} templates in Page.text setter (T262136, T267770)
* Remove deprecated UserBlocked exception and Page.contributingUsers()
* Add support for some 'wbset' actions in DataSite
* Fix UploadRobot site attribute (T267573)
* Ignore UnicodeDecodeError on input (T258143)
* Replace 'source' exception regex with 'syntaxhighlight' (T257899)
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
