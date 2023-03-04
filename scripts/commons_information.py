#!/usr/bin/env python3
"""Insert a language template into the description field."""
#
# (C) Pywikibot team, 2015-2023
#
# Distributed under the terms of the MIT license.
#
import copy

import mwparserfromhell

import pywikibot
from pywikibot import i18n, pagegenerators
from pywikibot.bot import ExistingPageBot, SingleSiteBot


try:
    import langdetect
except ImportError:
    langdetect = None


class InformationBot(SingleSiteBot, ExistingPageBot):

    """Bot for the Information template."""

    lang_tmp_cat = 'Language templates'
    desc_params = ('Description', 'description')

    comment = {
        'en': ('Bot: wrap the description parameter of Information in the '
               'appropriate language template')
    }

    def __init__(self, **kwargs) -> None:
        """Initialzer."""
        super().__init__(**kwargs)
        lang_tmp_cat = pywikibot.Category(self.site, self.lang_tmp_cat)
        self.lang_tmps = lang_tmp_cat.articles(namespaces=[10])

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
    def detect_langs(text):
        """Detect language from griven text."""
        if langdetect is not None:
            return langdetect.detect_langs(text)
        return None

    def process_desc_template(self, template) -> bool:
        """Process description template."""
        tmp_page = pywikibot.Page(self.site, template.name.strip(), ns=10)
        if tmp_page in self.lang_tmps and len(template.params) == 1 \
           and template.has('1'):
            lang_tmp_val = template.get('1').value.strip()
            langs = self.detect_langs(lang_tmp_val)
            if langs and langs[0].prob > 0.9:
                tmp_page2 = pywikibot.Page(self.site, langs[0].lang, ns=10)
                if tmp_page2 != tmp_page:
                    pywikibot.info(
                        '<<lightblue>>The language template {before!r} '
                        'was found, but langdetect thinks {after!r} is the '
                        'most appropriate with a probability of {prob}:'
                        '<<default>>\n{text}'
                        .format(before=tmp_page.title(with_ns=False),
                                after=tmp_page2.title(with_ns=False),
                                prob=langs[0].prob,
                                text=lang_tmp_val))
                    choice = pywikibot.input_choice(
                        'What to do?',
                        [('Replace it', 'r'), ('Do not replace it', 'n'),
                         ('Choose another', 'c')])
                    if choice == 'r':
                        template.name = langs[0].lang
                        return True

                    if choice == 'c':
                        newlang = pywikibot.input(
                            'Enter the language of the displayed text:')
                        if newlang and newlang != template.name:
                            template.name = newlang
                            return True
        return False

    @staticmethod
    def replace_value(param, value) -> None:
        """Replace param with given value."""
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
            if not page.site.sametitle(template.name.strip(), 'Information'):
                continue
            desc = self.get_description(template)
            if desc is None:
                continue
            for tmp in desc.value.filter_templates(recursive=False):
                if self.process_desc_template(tmp):
                    edited = True
            desc_clean = copy.deepcopy(desc.value)
            for tmp in desc_clean.filter_templates(recursive=False):
                # TODO: emit a debug item?
                desc_clean.remove(tmp)
            value = desc_clean.strip()
            if value == '':
                pywikibot.info('Empty description')
                continue
            pywikibot.info(value)
            langs = self.detect_langs(value)
            if langs:
                pywikibot.info('<<lightblue>>Hints from langdetect:')
                for language in langs:
                    pywikibot.info(
                        f'<<lightblue>>{language.lang}: {language.prob}')
            lang = pywikibot.input(
                'Enter the language of the displayed text:').strip()
            if lang != '':
                tmp_page = pywikibot.Page(page.site, lang, ns=10)
                if tmp_page not in self.lang_tmps:
                    pywikibot.warning(
                        '"{lang}" is not a valid language template on {site}'
                        .format(lang=lang, site=page.site))
                new = mwparserfromhell.nodes.template.Template(lang, [value])
                self.replace_value(desc, new)
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
    local_args = pywikibot.handle_args(args)
    gen_factory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        gen_factory.handle_arg(arg)

    gen = gen_factory.getCombinedGenerator()
    if gen:
        bot = InformationBot(generator=gen)
        bot.run()
    else:
        pywikibot.bot.suggest_help(missing_generator=True)


if __name__ == '__main__':
    main()
