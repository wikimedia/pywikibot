Current release changes
~~~~~~~~~~~~~~~~~~~~~~~

Breaking changes
^^^^^^^^^^^^^^^^

* config.db_hostname has been renamed to db_hostname_format

Other changes
^^^^^^^^^^^^^

* (no changes yet)

Future release notes
~~~~~~~~~~~~~~~~~~~~

* 5.6.0: comms.http.request() will return a requests.Response object rather than plain text (T265206)
* 5.6.0: comms.threadedhttp module will be removed (T265206)
* 5.6.0: APISite.loadimageinfo will no longer return any content
* 5.6.0: pagenenerators.handleArg() method will be removed in favour of handle_arg() (T271437)
* 5.5.0: Deprecated data attribute of http.fetch() result will be given up (T265206)
* 5.5.0: Site.getuserinfo() method will be dropped in favour of userinfo property
* 5.5.0: Site.getglobaluserinfo() method will be dropped in favour of globaluserinfo property
* 5.4.0: Support of MediaWiki < 1.23 will be dropped with release 6.0  (T268979)
* 5.4.0: LoginManager.getCookie() is deprecated and will be removed
* 5.4.0: tools.PY2 will be removed (T213287)
* 5.3.0: LogEntryFactory.logtypes property will be removed
* 5.3.0: toStdout parameter of logging.output()/pywikibot.output() function will be desupported
* 5.0.0: OptionHandler.options dict will be removed in favour of OptionHandler.opt
* 5.0.0: Methods deprecated for 5 years or longer will be removed
* 5.0.0: pagegenerators.ReferringPageGenerator is desupported and will be removed
