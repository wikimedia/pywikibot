Current release 8.0.0
---------------------

Improvements
^^^^^^^^^^^^

* Support federated Wikibase (:phab:`T173195`)
* Improve warning if a Non-JSON response was received from server (:phab:`T326046`)
* Allow normalization of :class:`pywikibot.WbTime` objects (:phab:`T123888`)
* Add parser for ``<pages />`` tag to :mod:`proofreadpage`
* ``addOnly`` parameter of :func:`textlib.replaceLanguageLinks` and :func:`textlib.replaceCategoryLinks`
  were renamed to ``add_only``
* ``known_codes`` attribute was added to :class:`family.WikimediaFamily` (:phab:`T325426`)
* Unify representation for :class:`time.Timestamp` between  CPython and Pypy (:phab:`T325905`)
* Implement comparison for :class:`pywikibot.WbTime` object (:phab:`T148280`, :phab:`T325863`)
* Create a cookie file for each account (:phab:`T324000`)
* Move data.api._login.LoginManager to :class:`login.ClientLoginManager`
* Let user the choice which section to be copied with :mod:`generate_user_files
  <pywikibot.scripts.generate_user_files>` (:phab:`T145372`)
* use :func:`roundrobin_generators<tools.itertools.roundrobin_generators>` to combine generators
  when limit option is given
* Ignore OSError if API cache cannot be written
* Update tools._unidata._category_cf from Unicodedata version 15.0.0
* :meth:`Timestamp.set_timestamp()<pywikibot.time.Timestamp.set_timestamp>` raises TypeError
  instead of ValueError if conversion fails
* Python 3.12 is supported
* All parameters of :meth:`APISite.categorymembers()
  <pywikibot.site._generators.GeneratorsMixin.categorymembers>` are provided with
  :meth:`Category.members()<page.Category.members>`,
  :meth:`Category.subcategories()<page.Category.subcategories>` (*member_type* excluded) and
  :meth:`Category.articles()<page.Category.articles>` (*member_type* excluded)
* Enable site-package installation from git repository (:phab:`T320851`)
* Enable 2FA login (:phab:`T186274`)
* :meth:`Page.editTime()<page.BasePage.editTime>` was replaced by
  :attr:`Page.latest_revision.timestamp<page.BasePage.latest_revision>`
* Raise a generic ServerError if requests response is a ServerError (:phab:`T320590`)
* Add a new variable 'private_folder_permission' to config.py (:phab:`T315045`)
* L10N and i18n updates
* Adjust subprocess args in :mod:`tools.djvu`
* Short site value can be given if site code is equal to family like ``-site:meta`` or ``-site:commons``

Documentation improvements
^^^^^^^^^^^^^^^^^^^^^^^^^^

* Add highlighting to targeted code snippet within documentation (:phab:`T323800`)
* Add previous, next, index, and modules links to documentation sidebar (:phab:`T323803`)
* Introduce standard colors (legacy palette) in Furo theme (:phab:`T323802`)
* Improve basic content structure and navigation of documentation (:phab:`T323812`)
* Use ``Furo`` sphinx theme instead of ``Natural`` and improve documentation look and feel (:phab:`T322212`)
* MediaWiki API cross reference was added to the documentation

Bugfixes
^^^^^^^^

* Don't raise StopIteration in :meth:`login.LoginManager.check_user_exists`
  if given user is behind the last user (:phab:`T326063`)
* Normalize :class:`WbTimes<pywikibot.WbTime>` sent to Wikidata (:phab:`T325860`)
* Fix :class:`pywikibot.WbTime` precision (:phab:`T324798`)
* Unquote title for red-links in class:`proofreadpage.IndexPage`
* Find month with first letter uppercase or lowercase with :class:`textlib.TimeStripper` (:phab:`T324310`)
* Fix disolving script_paths for site-package (:phab:`T320530`)
* Respect limit argument with Board.topics() (:phab:`T138215`, :phab:`T138307`)

Breaking changes
^^^^^^^^^^^^^^^^

* All parameters of :meth:`Category.members()<page.Category.members>`,
  :meth:`Category.subcategories()<page.Category.subcategories>` and
  :meth:`Category.articles()<page.Category.articles>` are keyword only
* The ``parent_id`` and ``content_model`` attributes of :class:`page.Revision` were removed in favour
  of ``parentid`` and ``contentmodel``
* Support for MediaWiki < 1.27 was dropped
* ListBoxWindows class of :mod:`userinterfaces.gui` was removed
* Require Python 3.6.1+ with Pywikibot and drop support for Python 3.6.0 (:phab:`T318912`)
* pymysql >= 0.9.3 is required (:phab:`T216741`)
* Python 3.5 support was dropped (:phab:`T301908`)
* *See also Code cleanups below*

Code cleanups
^^^^^^^^^^^^^
* ``maintenance/sorting_order`` script was removed (:phab:`T325426`)
* ``alphabetic_sv`` and ``interwiki_putfirst`` attributes of
  :class:`Wiktionary<families.wiktionary_family.Family>` family were removed (:phab:`T325426`)
* ``alphabetic``, ``alphabetic_revised`` and ``fyinterwiki`` attributes of :class:`family.Family`
  were removed (:phab:`T325426`)
* *See also Deprecations below*

Deprecations
------------

* 8.0.0: :meth:`Timestamp.clone()<pywikibot.time.Timestamp.clone>` method is deprecated
  in favour of ``Timestamp.replace()`` method.
* 8.0.0: :meth:`family.Family.maximum_GET_length` method is deprecated in favour of
  :ref:`config.maximum_GET_length<Account Settings>` (:phab:`T325957`)
* 8.0.0: ``addOnly`` parameter of :func:`textlib.replaceLanguageLinks` and
  :func:`textlib.replaceCategoryLinks` are deprecated in favour of ``add_only``
* 8.0.0: :class:`textlib.TimeStripper` regex attributes ``ptimeR``, ``ptimeznR``, ``pyearR``, ``pmonthR``,
  ``pdayR`` are deprecated in favour of ``patterns`` attribute which is a
  :class:`textlib.TimeStripperPatterns`.
* 8.0.0: :class:`textlib.TimeStripper` ``groups`` attribute is deprecated in favour of ``textlib.TIMEGROUPS``
* 8.0.0: :meth:`LoginManager.get_login_token<login.ClientLoginManager.get_login_token>` was
  replaced by ``login.ClientLoginManager.site.tokens['login']``
* 8.0.0: ``data.api.LoginManager()`` is deprecated in favour of :class:`login.ClientLoginManager`
* 8.0.0: :meth:`APISite.messages()<pywikibot.site._apisite.APISite.messages>` method is deprecated in favour of
  :attr:`userinfo['messages']<pywikibot.site._apisite.APISite.userinfo>`
* 8.0.0: :meth:`Page.editTime()<page.BasePage.editTime>` method is deprecated and should be replaced by
  :attr:`Page.latest_revision.timestamp<page.BasePage.latest_revision>`
* 7.7.0: :mod:`tools.threading` classes should no longer imported from :mod:`tools`
* 7.6.0: :mod:`tools.itertools` datatypes should no longer imported from :mod:`tools`
* 7.6.0: :mod:`tools.collections` datatypes should no longer imported from :mod:`tools`
* 7.5.0: :mod:`textlib`.tzoneFixedOffset class will be removed in favour of :class:`time.TZoneFixedOffset`
* 7.4.0: ``FilePage.usingPages()`` was renamed to :meth:`using_pages()<pywikibot.FilePage.using_pages>`
* 7.2.0: ``tb`` parameter of :func:`exception()<pywikibot.exception>` function was renamed to ``exc_info``
* 7.2.0: XMLDumpOldPageGenerator is deprecated in favour of a ``content`` parameter of
  :func:`XMLDumpPageGenerator<pagegenerators.XMLDumpPageGenerator>` (:phab:`T306134`)
* 7.2.0: RedirectPageBot and NoRedirectPageBot bot classes are deprecated in favour of
  :attr:`use_redirects<bot.BaseBot.use_redirects>` attribute
* 7.2.0: :func:`tools.formatter.color_format<tools.formatter.color_format>` is deprecated and will be removed
* 7.1.0: Unused `get_redirect` parameter of Page.getOldVersion() will be removed
* 7.1.0: APISite._simple_request() will be removed in favour of APISite.simple_request()
* 7.0.0: User.isBlocked() method is renamed to is_blocked for consistency
* 7.0.0: Private BaseBot counters _treat_counter, _save_counter, _skip_counter will be removed in favour of collections.Counter counter attribute
* 7.0.0: A boolean watch parameter in Page.save() is deprecated and will be desupported
* 7.0.0: baserevid parameter of editSource(), editQualifier(), removeClaims(), removeSources(), remove_qualifiers() DataSite methods will be removed
* 7.0.0: Values of APISite.allpages() parameter filterredir other than True, False and None are deprecated
* 7.0.0: The i18n identifier 'cosmetic_changes-append' will be removed in favour of 'pywikibot-cosmetic-changes'
* 6.5.0: OutputOption.output() method will be removed in favour of OutputOption.out property
* 6.5.0: Infinite rotating file handler with logfilecount of -1 is deprecated
* 6.4.0: 'allow_duplicates' parameter of :func:`tools.itertools.intersect_generators` as positional argument is deprecated, use keyword argument instead
* 6.4.0: 'iterables' of :func:`tools.itertools.intersect_generators` given as a list or tuple is deprecated, either use consecutive iterables or use '*' to unpack
* 6.2.0: outputter of OutputProxyOption without out property is deprecated
* 6.2.0: ContextOption.output_range() and HighlightContextOption.output_range() are deprecated
* 6.2.0: Error messages with '%' style is deprecated in favour for str.format() style
* 6.2.0: page.url2unicode() function is deprecated in favour of tools.chars.url2string()
* 6.2.0: Throttle.multiplydelay attribute is deprecated
* 6.2.0: SequenceOutputter.format_list() is deprecated in favour of 'out' property
* 6.0.0: config.register_family_file() is deprecated
* 5.5.0: APISite.redirectRegex() will be removed in favour of APISite.redirect_regex()
