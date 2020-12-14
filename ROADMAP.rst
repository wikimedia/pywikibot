Current release changes
~~~~~~~~~~~~~~~~~~~~~~~

* DataSite.get_item() method will be removed
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

Future release notes
~~~~~~~~~~~~~~~~~~~~

* 5.1.0: Positional arguments of page.Revision must be replaced by keyword arguments (T259428)
* 5.0.0: wikistats methods fetch, raw_cached, csv, xml will be removed
* 5.0.0: PageRelatedError.getPage() will be removes in favour of PageRelatedError.page
* 5.0.0: HttpRequest result of http.fetch() will be replaced by requests.Response (T265206)
* 5.0.0: OptionHandler.options dict will be removed in favour of OptionHandler.opt
* 5.0.0: Methods deprecated for 5 years or longer will be removed
* 5.0.0: Outdated recentchanges parameter will be removed
* 5.0.0: site.LoginStatus will be removed in favour of login.LoginStatus
* 5.0.0: pagegenerators.ReferringPageGenerator is desupported and will be removed
