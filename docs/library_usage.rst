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
      All pages from the generator that do not exist are skipped.
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
      instantiating it are accessible via
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
:25:  Local options which are available for the current bot are
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


Creating Lexemes
================

A new :class:`pywikibot.LexemePage` can be saved with either an explicit
creation dictionary or fields populated on the object. Wikibase requires
at least one lemma, a language item and a lexical category item. The server
validates these fields and any optional forms, senses and statements.

The examples below assume ``repo`` is your configured Wikibase repository
with WikibaseLexeme installed, and ``language_id`` and ``category_id`` are
existing item IDs in that repository. Saving writes to that repository.

To supply an explicit creation dictionary:

.. code-block:: python

    import pywikibot

    lexeme = pywikibot.LexemePage(repo)
    lexeme.editEntity({
        'lemmas': {'en': 'colour'},
        'language': language_id,
        'lexicalCategory': category_id,
        'forms': [{
            'add': '',
            'representations': {'en': 'colours'},
            'grammaticalFeatures': [],
        }],
        'senses': [{'add': '', 'glosses': {'en': 'visual appearance'}}],
    }, summary='Create a Lexeme')
    print(lexeme.id)

Explicit data takes precedence: fields already set on the object are not
merged into the supplied dictionary. New forms and senses in an explicit
operation list require the ``add`` marker.

Alternatively, populate the object and save without a data argument:

.. code-block:: python

    lexeme = pywikibot.LexemePage(repo)
    lexeme.lemmas['en'] = 'colour'
    lexeme.language = pywikibot.ItemPage(repo, language_id)
    lexeme.lexicalCategory = pywikibot.ItemPage(repo, category_id)
    form = pywikibot.LexemeForm(repo)
    form.representations['en'] = 'colours'
    lexeme.forms.append(form)
    sense = pywikibot.LexemeSense(repo)
    sense.glosses['en'] = 'visual appearance'
    lexeme.senses.append(sense)
    lexeme.editEntity(summary='Create a Lexeme')

After a successful save, ``lexeme.id`` contains the assigned Lexeme ID.
Cached fields are invalidated and reloaded on access. Reacquire forms,
senses and claims from the parent to obtain their server-assigned IDs;
previously retained child objects remain snapshots. For example, use
``form = lexeme.forms[0]`` before editing that form again. Subsequent calls
to ``lexeme.editEntity()`` update the existing Lexeme.

A rejected creation leaves local fields available for correction. A lost
connection or timeout can instead leave the outcome unknown: the server
may have created the Lexeme even though no response arrived. Check the
repository before attempting another creation; retrying blindly can create
a duplicate. Matching lemmas alone do not establish an entry's identity.
Automatic recovery from uncertain write outcomes is not provided.
