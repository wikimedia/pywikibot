**************************
Using pywikibot as library
**************************

Pywikibot provides bot classes to develop your own script easily.

Minimal example
===============

Here is a minimal example script which shows their usage:

..  code-block:: python
    :linenos:
    :emphasize-lines: 5,12,18

    import pywikibot
    from pywikibot import pagegenerators
    from pywikibot.bot import ExistingPageBot

    class MyBot(ExistingPageBot):

        update_options = {
            'text': 'This is a test text',
            'summary': 'Bot: a bot test edit with Pywikibot.',
        }

        def treat_page(self):
            """Load the given page, do some changes, and save it."""
            text = self.current_page.text
            text += '\n' + self.opt.text
            self.put_current(text, summary=self.opt.summary)

    def main():
        """Parse command line arguments and invoke bot."""
        options = {}
        gen_factory = pagegenerators.GeneratorFactory()
        # Option parsing
        local_args = pywikibot.handle_args()  # global options
        local_args = gen_factory.handle_args(local_args)  # generators options
        for arg in local_args:
            opt, sep, value = arg.partition(':')
            if opt in ('-summary', '-text'):
                options[opt[1:]] = value
        MyBot(generator=gen_factory.getCombinedGenerator(), **options).run()

    if __name__ == '__main__':
        main()

The script can be invoked from commandline like::

    python mybot -site:wikipedia:test -page:Sandbox -text:"A text added to the sandbox"

Explanation
-----------

:1-3: Import necessary framework code parts:
      :mod:`pywikibot`, :mod:`pywikibot.pagegenerators`,
      :class:`bot.ExistingPageBot`.
:5:   The bot is derived from
      :class:`ExistingPageBot<bot.ExistingPageBot>`.
      All pages from  generator which does not exists are skipped.
:7:   Every Bot has an *always* option which autoconfirms any changes if
      set to True. To expand all available options of a bot and set the
      default values of them, use
      :attr:`update_options<bot.BaseBot.update_options>`
      attribute or update
      :attr:`available_options<bot.BaseBot.available_options>`
      like it is shown in :ref:`BasicBot<Basic script>` below.
:12:  All changes for each page are made in this
      :meth:`treat_page<bot.CurrentPageBot.treat_page>` method.
:14:  :attr:`current_page<bot.BaseBot.current_page>` is the current
      :class:`pywikibot.Page` object from
      :attr:`generator<bot.BaseBot.generator>`.
:15:  All bot options which are passed to the bot class when
      instantiating it are accessable via
      :class:`opt attribute<bot.OptionHandler>`. ``opt.always``,
      ``opt.text`` and ``opt.summary`` are all available options for this
      bot class.
:16:  Save the changes to the live wiki with
      :meth:`put_current<bot.CurrentPageBot.put_current>`.
:18:  Parse command line options inside this function.
:20:  A dict which holds all options for the bot.
:21:  :py:obj:`pagegenerators.GeneratorFactory` supports
      generators and filter options.
:23:  Pywikibot provides :ref:`global options<Global Options>` like site
      specification or a *simulate* switch to prevent live wiki changes.
      These options are parsed by :func:`pywikibot.handle_args`.
:24:  :ref:`Generators<Generator Options>` and
      :ref:`filter options<Filter Options>` of
      :mod:`pywikibot.pagegenerators` are parsed here using
      :meth:`GeneratorFactory.handle_args()
      <pagegenerators.GeneratorFactory.handle_args>`.
:25:  Local options which are are available for the current bot are
      parsed in this loop.
:29:  Create the bot passing keyword only parameters and run it.

Basic script
============

:py:obj:`scripts.basic` is a more advanced sample script and shipped
with the scripts folder. Here is the content:

.. literalinclude:: ../scripts/basic.py
   :language: python

.. note::
   Also see the documentation at :manpage:`Create your own script`
