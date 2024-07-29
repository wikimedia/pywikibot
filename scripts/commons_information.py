#!/usr/bin/env python3
"""This bot adds a language template to the file's description field.

The ``Information`` template is commonly used to provide formatting to
the basic information for files (description, source, author, etc.). The
``description`` field should provide brief but complete information
about the image. The description format should use Language templates
like ``{{En}}`` or ``{{De}}`` to specify the language of the description.
This script adds these langage templates if missing. For example the
description of

.. code-block:: wikitext

   {{Information
    | Description = A simplified icon for [[Pywikibot]]
    | Date = 2003-06-14
    | Other fields =
   }}

will be analyzed as ``en`` language by ~100 % accurancy and the bot
replaces its content by

.. code-block:: wikitext
   :emphasize-lines: 2

   {{Information
    | Description = {{en|A simplified icon for [[Pywikibot]]}}
    | Date = 2003-06-14
    | Other fields =
   }}

.. note:: ``langdetect`` package is needed for fully support of language
   detection. Install it with::

       pip install langdetect

This script understands the following command-line arguments:

&params;

Usage:

    python pwb.py commons_information [pagegenerators]

You can use any typical pagegenerator (like categories) to provide with
a list of pages. If no pagegenerator is given, transcluded pages from
``Information`` template are used.

.. hint:: This script uses ``commons`` site as default. For other sites
   use the global ``-site`` option.

Example for going through all files:

    python pwb.py commons_information -start:File:!

.. versionadded:: 6.0
.. versionchanged:: 9.2
   accelerate script with preloading pages; use ``commons`` as default
   site; use transcluded pages of ``Information`` template.
"""
#
# (C) Pywikibot team, 2015-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

from textwrap import fill

import mwparserfromhell

import pywikibot
from pywikibot import config, i18n, pagegenerators
from pywikibot.bot import ExistingPageBot, SingleSiteBot


# This is required for the text that is shown when you run this script
# with the parameter -help or without parameters.
docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816

try:
    import langdetect
except ImportError:
    langdetect = None


INFORMATION_TMPL = 'Information'


class InformationBot(SingleSiteBot, ExistingPageBot):

    """Bot for the Information template."""

    lang_tmp_cat = 'Language templates'
    desc_params = ('Description', 'description')

    comment = {
        'en': (f'Bot: wrap the description parameter of {INFORMATION_TMPL} in'
               ' the appropriate language template')
    }

    def __init__(self, **kwargs) -> None:
        """Initialzer."""
        super().__init__(**kwargs)
        lang_tmp_cat = pywikibot.Category(self.site, self.lang_tmp_cat)
        self.lang_tmps = {t.title(with_ns=False).lower()
                          for t in lang_tmp_cat.articles(namespaces=[10])}

    def get_description(self, template):
        """Get description parameter."""
        params = [param for param in template.params
                  if param.name.strip() in self.desc_params]
        if len(params) > 1:
            pywikibot.warning('multiple description parameters found')
        elif len(params) == 1 and params[0].value.strip() != '':
            return params[0]
        return None

    @staticmethod
    def detect_langs(text: str):
        """Detect language from given text."""
        if langdetect is not None:
            return langdetect.detect_langs(text)
        return None

    def process_desc_template(
        self,
        template: mwparserfromhell.nodes.template.Template
    ) -> bool:
        """Process description template.

        :param template: a mwparserfromhell Template found in the
            description parameter of ``Information`` template.
        :return: whether the *template* node was changed.
        """
        tmpl_lang = template.name.strip().lower()
        if tmpl_lang in self.lang_tmps and len(template.params) == 1 \
           and template.has('1'):
            lang_tmp_val = template.get('1').value.strip()
            langs = self.detect_langs(lang_tmp_val)
            if not langs:
                return False

            lang, prob = langs[0].lang, langs[0].prob
            if lang != tmpl_lang and prob > 0.9 and lang in self.lang_tmps:
                pywikibot.info(
                    f'<<lightblue>>The language template {tmpl_lang!r} '
                    f'was found, but language detection thinks {lang!r}\n'
                    f'is the most appropriate with a probability of {prob}:'
                )
                pywikibot.info(fill(lang_tmp_val, width=78))
                while True:
                    choice = pywikibot.input_choice(
                        'What to do?',
                        [
                            ('Replace it', 'r'),
                            ('Do not replace it', 'n'),
                            ('Choose another', 'c'),
                        ],
                        default='n',
                    )
                    if choice == 'n':
                        break

                    if choice == 'r':
                        template.name = lang
                        return True

                    # choice == 'c':
                    newlang = pywikibot.input(
                        'Enter the language of the displayed text:').strip()
                    if not newlang or newlang == tmpl_lang:
                        break

                    if newlang in self.lang_tmps:
                        template.name = newlang
                        return True

                    pywikibot.warning(f'<<lightred>>{newlang!r} is not a valid'
                                      f' language template on {self.site}')
        return False

    def process_desc_other(self,
                           wikicode: mwparserfromhell.wikicode.Wikicode,
                           nodes: list[mwparserfromhell.nodes.Node]) -> bool:
        """Process other description text.

        The description text may consist of different Node types except
        of Template which is handled by :meth:`process_desc_template`.
        Combine all nodes and replace the last with new created
        Template while removing the remaining from *wikicode*.

        .. versionadded:: 9.2

        :param wikicode: The Wikicode of the parsed page text.
        :param nodes: wikitext nodes to be processed
        :return: whether the description nodes were changed
        """
        if type(nodes[0]).__name__ == 'Text' and nodes[0].value.isspace():
            # ignore the first node with spaces only
            nodes = nodes[1:]

        value = ''.join(str(node) for node in nodes).strip()
        if not value:
            return False

        pywikibot.info(fill(value, 78))
        langs = self.detect_langs(value)

        if langs:
            pywikibot.info('<<lightblue>>Hints from langdetect:')
            for language in langs:
                pywikibot.info(
                    f'<<lightblue>>{language.lang}: {language.prob}')

        while True:
            lang = pywikibot.input(
                'Enter the language of the displayed text:').strip()

            if not lang:
                return False

            if lang in self.lang_tmps:
                break

            pywikibot.warning(f'<<lightred>>{lang!r} is not a valid language '
                              f'template on {self.site}')

        # replace the last node
        new = mwparserfromhell.nodes.template.Template(lang, [value.rstrip()])
        try:
            self.replace_value(nodes[-1], new)
        except AttributeError:
            # Node is has no value attribute, add the template directly
            wikicode.insert_after(nodes[-1], str(new))
            wikicode.remove(nodes[-1])

        # remove the other nodes
        for node in nodes[:-1]:
            node = wikicode.remove(node)

        return True

    @staticmethod
    def replace_value(param: mwparserfromhell.nodes.Node,
                      value: mwparserfromhell.nodes.template.Template) -> None:
        """Replace *param* node with given value."""
        lstrip = param.value.lstrip()
        lspaces = param.value[:len(param.value) - len(lstrip)]
        rspaces = lstrip[len(lstrip.rstrip()):]
        param.value = f'{lspaces}{value}{rspaces}'

    def treat_page(self) -> None:
        """Treat current page."""
        page = self.current_page
        code = mwparserfromhell.parse(page.text)
        edited = False  # to prevent unwanted changes

        for template in code.ifilter_templates():
            if not page.site.sametitle(template.name.strip(),
                                       INFORMATION_TMPL):
                continue

            desc = self.get_description(template)
            if desc is None:
                continue

            unhandled = []
            for node in desc.value.nodes:
                node_type = type(node).__name__

                if node_type == 'Comment':
                    pass
                elif node_type == 'Template':

                    # first handle unhandled nodes
                    if unhandled:
                        if self.process_desc_other(code, unhandled):
                            edited = True
                        unhandled = []

                    # now process hte template
                    if self.process_desc_template(node):
                        edited = True
                else:
                    unhandled.append(node)

            if unhandled and self.process_desc_other(code, unhandled):
                edited = True

        if edited:
            text = str(code)
            summary = i18n.translate(page.site.lang, self.comment,
                                     fallback=True)
            self.put_current(text, summary=summary)


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    # set default family to commons
    config.mylang = config.family = 'commons'

    local_args = pywikibot.handle_args(args)
    gen_factory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        gen_factory.handle_arg(arg)

    site = pywikibot.Site()
    gen = gen_factory.getCombinedGenerator(preload=True)
    if not gen:
        tmpl = pywikibot.Page(site, INFORMATION_TMPL,
                              ns=site.namespaces.TEMPLATE)
        gen = tmpl.getReferences(only_template_inclusion=True,
                                 namespaces=site.namespaces.FILE,
                                 content=True)
    bot = InformationBot(site=site, generator=gen)
    bot.run()


if __name__ == '__main__':
    main()
