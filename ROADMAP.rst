Current release changes
~~~~~~~~~~~~~~~~~~~~~~~

* Avoid conflicts between site and possible site keyword in api.Request.create_simple() (T262926)
* Remove wrong param of rvision() call in Page.latest_revision_id
* Do not raise Exception in Page.get_best_claim() but follow redirect (T265839)
* xml-support of wikistats will be dropped
* Remove deprecated mime_params in api.Request()
* cleanup interwiki_graph.py and replace deprecated originPage by origin in Subjects
* Upload a file that ends with the '\r' byte (T132676)
* Fix incorrect server time (T266084)
* L10N-Updates
* Support Namespace packages in version.py (T265946)
* Server414Error was added to pywikibot (T266000)
* Deprecated editor.command() method was removed
* comms.PywikibotCookieJar and comms.mode_check_decorator were deleted
* Remove deprecated tools classes Stringtypes and UnicodeType
* Remove deprecated tools function open_compressed and signature and UnicodeType class
* Fix http_tests.LiveFakeUserAgentTestCase (T265842)
* HttpRequest properties were renamed to request.Response identifiers (T265206)


Future release notes
~~~~~~~~~~~~~~~~~~~~

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
