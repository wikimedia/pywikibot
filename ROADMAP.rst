Current release changes
~~~~~~~~~~~~~~~~~~~~~~~

* Allow using pywikibot as site-package without user-config.py (T270474)
* Python 3.10 is supported
* Fix AutoFamily scriptpath() call (T270370)
* Add support for skrwiki, skrwiktionary, eowikivoyage, wawikisource, madwiki (T268414, T268460, T269429, T269434, T269442)
* wikistats methods fetch, raw_cached, csv, xml has been removed
* PageRelatedError.getPage() has been removed in favour of PageRelatedError.page
* DataSite.get_item() method has been removed
* global put_throttle option may be given as float (T269741)
* Property.getType() method has been removed
* Family.server_time() method was removed; it is still available from Site object (T89451)
* All HttpRequest parameters except of charset has been dropped (T265206)
* A lot of methods and properties of HttpRequest are deprecared in favour of requests.Resonse attributes (T265206)
* Method and properties of HttpRequest are delegated to requests.Response object (T265206)
* comms.threadedhttp.HttpRequest.raw was replaced by HttpRequest.content property (T265206)
* Desupported version.getfileversion() has been removed
* site parameter of comms.http.requests() function is mandatory and cannot be omitted
* date.MakeParameter() function has been removed
* api.Request.http_params() method has been removed
* L10N updates

Future release notes
~~~~~~~~~~~~~~~~~~~~

* 5.3.0: api.ParamInfo.modules property will be removed
* 5.3.0: LogEntryFactory.logtypes property will be removed
* 5.3.0: stdout parameter of logging.output()/pywikibot.output() function will be desupported
* 5.1.0: Positional arguments of page.Revision must be replaced by keyword arguments (T259428)
* 5.0.0: HttpRequest result of http.fetch() will be replaced by requests.Response (T265206)
* 5.0.0: OptionHandler.options dict will be removed in favour of OptionHandler.opt
* 5.0.0: Methods deprecated for 5 years or longer will be removed
* 5.0.0: Outdated Site.recentchanges() parameters will be removed
* 5.0.0: site.LoginStatus will be removed in favour of login.LoginStatus
* 5.0.0: pagegenerators.ReferringPageGenerator is desupported and will be removed
