************
Introduction
************

.. include:: ../README.rst
   :end-before: For more documentation on Pywikibot
   :start-line: 41

Settings
========

It is recommended to create a `user-config.py` file if Pywikibot is used as a
site package. If Pywikibot is used in directory mode e.g. from a repository
the configuration file is mandatory. A minimal sample is shown below.

.. literalinclude:: ../user-config.py.sample

This sample is shipped with the repository but is not available with
the site-package. For more settings use
:mod:`generate_user_files<pywikibot.scripts.generate_user_files>` script
or refer :py:mod:`pywikibot.config` module.

.. seealso:: :manpage:`Installation` Manual


Internationalisation (i18n)
===========================

Some of the framework input interaction is translated. The user interface
language to be used can be set as follows:

#. set the `userinterface_lang` in your :ref:`user-config.py<User Interface Settings>` to your preferred language
#. set environment variable `PYWIKIBOT_USERINTERFACE_LANG` to your preferred language
#. default is obtained from `locale.getlocale`
#. fallback is `'en'` for English if all other options fails

.. note:: The preferred language code must follow ISO 639.
.. versionadded:: 7.0
   Added to site-package distribution
.. seealso::
   * :manpage:`i18n` Manual
   * `MediaWiki Language Codes <https://www.mediawiki.org/wiki/Manual:Language#Language_code>`_
   * :ref:`User Interface Settings`
   * :py:mod:`pywikibot.i18n`
