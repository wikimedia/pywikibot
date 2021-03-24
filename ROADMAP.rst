Current release changes
~~~~~~~~~~~~~~~~~~~~~~~

* L10N updates
* Family files can be collected from a zip folder (T278076)
* Deprecated getuserinfo and getglobaluserinfo Site methods were removed
* compat2core.py script was archived

Future release notes
~~~~~~~~~~~~~~~~~~~~

* 6.0.0: User.name() method will be removed in favour of User.username property
* 5.6.0: pagenenerators.handleArg() method will be removed in favour of handle_arg() (T271437)
* 5.6.0: Family.ignore_certificate_error() method will be removed in favour of verify_SSL_certificate() (T265205)
* 5.0.0: OptionHandler.options dict will be removed in favour of OptionHandler.opt
* 5.0.0: Methods deprecated for 5 years or longer will be removed
* 5.0.0: pagegenerators.ReferringPageGenerator is desupported and will be removed
