**************************
Frequently asked questions
**************************


**How to speed up Pywikibot?**
  * If you need the content, use :py:mod:`PreloadingGenerator
    <pagegenerators.PreloadingGenerator>` with page generators,
    :func:`PreloadingEntityGenerator <pagegenerators.PreloadingEntityGenerator>`
    for wikibase entities and :py:mod:`DequePreloadingGenerator
    <pagegenerators.DequePreloadingGenerator>` for a
    :py:mod:`DequeGenerator <tools.collections.DequeGenerator>`.
  * If you use :py:mod:`GeneratorFactory
    <pagegenerators.GeneratorFactory>` with your bot and use its
    :py:mod:`getCombinedGenerator
    <pagegenerators.GeneratorFactory.getCombinedGenerator>` method
    you can set ``preload=True`` to preload page content. This is an alternate
    to the ``PreloadingGenerator`` function mentioned above.
  * Use :func:`MySQLPageGenerator
    <pagegenerators.MySQLPageGenerator>` if direct DB access is
    available and appropriate. See also: :manpage:`MySQL`

**The bot cannot delete pages**
  Your account needs delete rights on your wiki. If you have setup another
  account in your user_config use ``-user``
  :ref:`global options` to change it.
  Maybe you have to login first.

**ERROR: Unable to execute script because no *generator* was defined.**
  Using ``-help`` option is a good way to find all generators which can be
  used  with that script. You can also find all generator options and filter
  options at :py:mod:`pywikibot.pagegenerators` module.
  See also :manpage:`Page Generators` for additional information.

**pywikibot.i18n.TranslationError: No English translation has been defined**
  It can happen due to lack of i18n submodule or files. Update i18n submodule
  or download these files first. See also: :manpage:`i18n` manual.
