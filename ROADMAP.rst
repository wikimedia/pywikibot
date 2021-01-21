Current release changes
~~~~~~~~~~~~~~~~~~~~~~~

* Add support for trwikivoyage (T271263)
* UI.input_list_choice() has been improved (T272237)
* Global handleArgs() function was removed in favour of handle_args
* Deprecated originPage and foundIn property has been removed in interwiki_graph.py
* ParamInfo modules, prefixes, query_modules_with_limits properties and module_attribute_map() method was removed
* Allow querying alldeletedrevisions with APISite.alldeletedrevisions() and User.deleted_contributions()
* data attribute of http.fetch() response is deprecated (T265206)
* Positional arguments of page.Revision aren't supported any longer (T259428)
* pagenenerators.handleArg() method was renamed to handle_arg() (T271437)
* Page methods deprecated for 6 years were removed
* Create a Site with AutoFamily if a family isn't predefined (T249087)

Future release notes
~~~~~~~~~~~~~~~~~~~~

* 5.6.0: APISite.loadimageinfo will no longer return any content
* 5.6.0: pagenenerators.handleArg() method will be removed in favour of handle_arg() (T271437)
* 5.5.0: Site.getuserinfo() method will be dropped in favour of userinfo property
* 5.5.0: Site.getglobaluserinfo() method will be dropped in favour of globaluserinfo property
* 5.4.0: Support of MediaWiki < 1.23 will be dropped with release 6.0  (T268979)
* 5.4.0: LoginManager.getCookie() is deprecated and will be removed
* 5.4.0: tools.PY2 will be removed (T213287)
* 5.3.0: LogEntryFactory.logtypes property will be removed
* 5.3.0: stdout parameter of logging.output()/pywikibot.output() function will be desupported
* 5.0.0: HttpRequest result of http.fetch() will be replaced by requests.Response (T265206)
* 5.0.0: OptionHandler.options dict will be removed in favour of OptionHandler.opt
* 5.0.0: Methods deprecated for 5 years or longer will be removed
* 5.0.0: pagegenerators.ReferringPageGenerator is desupported and will be removed
