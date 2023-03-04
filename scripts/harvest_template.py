#!/usr/bin/env python3
r"""
Template harvesting script.

Usage (see below for explanations and examples):

 python pwb.py harvest_template -transcludes:"..." \
    [default optional arguments] \
    template_parameter PID [local optional arguments] \
    [template_parameter PID [local optional arguments]]
 python pwb.py harvest_template [generators] -template:"..." \
    [default optional arguments] \
    template_parameter PID [local optional arguments] \
    [template_parameter PID [local optional arguments]]

This will work on all pages that transclude the template in the article
namespace

These command line parameters can be used to specify which pages to work on:

&params;

You can also use additional parameters:

-confirm            If used, the bot will ask if it should make changes

-create             Create missing items before importing.

The following command line parameters can be used to change the bot's behavior.
If you specify them before all parameters, they are global and are applied to
all param-property pairs. If you specify them after a param-property pair,
they are local and are only applied to this pair. If you specify the same
argument as both local and global, the local argument overrides the global one
(see also examples):

-islink           Treat plain text values as links ("text" -> "[[text]]").

-exists           If set to 'p', add a new value, even if the item already
                  has the imported property but not the imported value.
                  If set to 'pt', add a new value, even if the item already
                  has the imported property with the imported value and
                  some qualifiers.

-multi            If set, try to match multiple values from parameter.

-inverse          Import this property as the inverse claim.

Examples
--------

The following command will try to import existing images from "image"
parameter of "Infobox person" on English Wikipedia as Wikidata property
"P18" (image):

    python pwb.py harvest_template -lang:en -family:wikipedia -namespace:0 \
        -template:"Infobox person" image P18

The following command will behave the same as the previous example and also
try to import [[links]] from "birth_place" parameter of the same template
as Wikidata property "P19" (place of birth):

    python pwb.py harvest_template -lang:en -family:wikipedia -namespace:0 \
        -template:"Infobox person" image P18 birth_place P19

The following command will import both "birth_place" and "death_place"
params with -islink modifier, ie. the bot will try to import values, even
if it doesn't find a [[link]]:

    python pwb.py harvest_template -lang:en -family:wikipedia -namespace:0 \
        -template:"Infobox person" -islink birth_place P19 death_place P20

The following command will do the same but only "birth_place" can be
imported without a link:

    python pwb.py harvest_template -lang:en -family:wikipedia -namespace:0 \
        -template:"Infobox person" birth_place P19 -islink death_place P20

The following command will import an occupation from "occupation" parameter
of "Infobox person" on English Wikipedia as Wikidata property "P106"
(occupation). The page won't be skipped if the item already has that
property but there is not the new value:

    python pwb.py harvest_template -lang:en -family:wikipedia -namespace:0 \
        -template:"Infobox person" occupation P106 -exists:p

The following command will import band members from the "current_members"
parameter of "Infobox musical artist" on English Wikipedia as Wikidata
property "P527" (has part). This will only extract multiple band members
if each is linked, and will not add duplicate claims for the same member:

    python pwb.py harvest_template -lang:en -family:wikipedia -namespace:0 \
        -template:"Infobox musical artist" current_members P527 -exists:p \
        -multi

The following command will import the category's main topic from the first
anonymous parameter of "Cat main" on English Wikipedia as Wikidata property
"P301" (category's main topic) and whenever a new value is imported,
the inverse claim is imported to the topic item as Wikidata property "P910"
(topic's main category) unless a claim of that property is already there:

    python pwb.py harvest_template -lang:en -family:wikipedia -namespace:14 \
        -template:"Cat main" 1 P301 -inverse:P910 -islink

.. note:: This script is a
   :py:obj:`ConfigParserBot <bot.ConfigParserBot>`. All options
   can be set within a settings file which is scripts.ini by default.
.. versionadded:: 7.5
   the -inverse option.
"""
#
# (C) Pywikibot team, 2013-2022
#
# Distributed under the terms of MIT License.
#
import re
import signal
import sys
from typing import Any, Iterator, Optional

import pywikibot
from pywikibot import WbTime
from pywikibot import pagegenerators as pg
from pywikibot import textlib
from pywikibot.backports import List, Tuple
from pywikibot.bot import ConfigParserBot, OptionHandler, WikidataBot
from pywikibot.exceptions import (
    APIError,
    InvalidPageError,
    InvalidTitleError,
    NoPageError,
)


willstop = False


def _signal_handler(signum, frame) -> None:
    global willstop
    if not willstop:
        willstop = True
        pywikibot.info('Received ctrl-c. Finishing current item; '
                       'press ctrl-c again to abort.')
    else:
        raise KeyboardInterrupt


signal.signal(signal.SIGINT, _signal_handler)

docuReplacements = {'&params;': pywikibot.pagegenerators.parameterHelp}


class PropertyOptionHandler(OptionHandler):

    """Class holding options for a param-property pair."""

    available_options = {
        'exists': '',
        'islink': False,
        'multi': False,
        'inverse': None,
    }


class HarvestRobot(ConfigParserBot, WikidataBot):

    """A bot to add Wikidata claims.

    .. versionchanged:: 7.0
       HarvestRobot is a ConfigParserBot
    """

    update_options = {
        'always': True,
        'create': False,
        'exists': '',
        'islink': False,
        'multi': False,
        'inverse': None,
    }

    def __init__(self, template_title, fields, **kwargs) -> None:
        """Initializer.

        :param template_title: The template to work on
        :type template_title: str
        :param fields: A dictionary of fields that are of use to us
        :type fields: dict
        :keyword islink: Whether non-linked values should be treated as links
        :type islink: bool
        :keyword create: Whether to create a new item if it's missing
        :type create: bool
        :keyword exists: pattern for merging existing claims with harvested
            values
        :type exists: str
        :keyword multi: Whether multiple values should be extracted from a
            single parameter
        :type multi: bool
        :keyword inverse: a property to populate on the target, pointing to
            the page item
        :type inverse: str
        """
        super().__init__(**kwargs)
        self.fields = {}
        for key, value in fields.items():
            if isinstance(value, tuple):
                self.fields[key] = value
            else:  # backwards compatibility
                self.fields[key] = (value, PropertyOptionHandler())
        self.template_title = template_title.replace('_', ' ')
        self.linkR = textlib.compileLinkR()
        self.create_missing_item = self.opt.create

    def setup(self):
        """Cache some static data from wikis."""
        self.cacheSources()
        self.templateTitles = self.getTemplateSynonyms(self.template_title)

    def getTemplateSynonyms(self, title: str) -> List[str]:
        """Fetch redirects of the title, so we can check against them."""
        temp = pywikibot.Page(self.site, title, ns=10)
        if not temp.exists():
            sys.exit(f'Template {temp.title()} does not exist.')

        # Put some output here since it can take a while
        pywikibot.info('Finding redirects...')
        if temp.isRedirectPage():
            temp = temp.getRedirectTarget()
        titles = [page.title(with_ns=False)
                  for page in temp.getReferences(filter_redirects=True,
                                                 namespaces=[10],
                                                 follow_redirects=False)]
        titles.append(temp.title(with_ns=False))
        return titles

    @staticmethod
    def template_link_target(item: pywikibot.ItemPage,
                             site: pywikibot.site.BaseSite,
                             link_text: str) -> Optional[pywikibot.ItemPage]:
        """Find the ItemPage target for a given link text.

        .. versionchanged:: 7.5
           Only follow the redirect target if redirect page has no
           wikibase item.
        """
        linked_page = pywikibot.Page(site, link_text)
        try:
            exists = linked_page.exists()
        except (InvalidTitleError, InvalidPageError):
            pywikibot.error(
                f'"{link_text}" is not a valid title or the page itself is '
                f'invalid so it cannot be linked. Skipping.')
            return None

        if not exists:
            pywikibot.info(f'{linked_page} does not exist so it cannot be '
                           f'linked. Skipping.')
            return None

        while True:
            try:
                linked_item = pywikibot.ItemPage.fromPage(linked_page)
            except NoPageError:
                if linked_page.isRedirectPage():
                    linked_page = linked_page.getRedirectTarget()
                    continue
                linked_item = None
            break

        if not linked_item or not linked_item.exists():
            pywikibot.info(f'{linked_page} does not have a wikidata item to '
                           f'link with. Skipping.')
            linked_item = None
        elif linked_item.title() == item.title():
            pywikibot.info(f'{linked_page} links to itself. Skipping.')
            linked_item = None

        return linked_item

    def _get_option_with_fallback(self, handler, option) -> Any:
        """
        Compare bot's (global) and provided (local) options.

        .. seealso:: :class:`OptionHandler`
        """
        return handler.opt[option] or self.opt[option]

    def treat_page_and_item(self,
                            page: Optional[pywikibot.page.BasePage],
                            item: Optional[pywikibot.page.ItemPage]) -> None:
        """Process a single page/item."""
        if willstop:
            raise KeyboardInterrupt

        if page is None:
            return

        assert page is self.current_page

        templates = page.raw_extracted_templates
        for template, fielddict in templates:
            # Clean up template
            try:
                template = pywikibot.Page(page.site, template, ns=10)
            except InvalidTitleError:
                pywikibot.error(
                    'Failed parsing template; {!r} should be '
                    'the template name.'.format(template))
                continue

            if template.title(with_ns=False) not in self.templateTitles:
                continue

            # We found the template we were looking for
            for field_item in fielddict.items():
                self.treat_field(item, page.site, field_item)

    def treat_field(self,
                    item: pywikibot.page.ItemPage,
                    site: pywikibot.site.BaseSite,
                    field_item: Tuple[str, str]) -> None:
        """Process a single field of template fielddict.

        .. versionadded:: 7.5
        """
        field, value = field_item
        field = field.strip()
        if not field or field not in self.fields:
            return

        # todo: extend the list of tags to ignore
        value = textlib.removeDisabledParts(
            # todo: eventually we may want to import the references
            value, tags=['ref'], site=site).strip()

        if not value:
            return

        # This field contains something useful for us
        prop, options = self.fields[field]
        ppage = pywikibot.PropertyPage(self.repo, prop)
        handler = getattr(self, 'handle_'
                          + ppage.type.lower().replace('-', '_'), None)
        if not handler:
            pywikibot.info('{} is not a supported datatype.'
                           .format(ppage.type))
            return

        exists_arg = set(self._get_option_with_fallback(options, 'exists'))
        do_multi = self._get_option_with_fallback(options, 'multi')
        inverse_prop = self._get_option_with_fallback(options, 'inverse')

        for target in handler(value, site, item, field):
            claim = ppage.newClaim()
            claim.setTarget(target)
            # A generator might yield pages from multiple sites
            added = self.user_add_claim_unless_exists(
                item, claim, exists_arg, site, pywikibot.info)

            if (added and inverse_prop
                    and isinstance(target, pywikibot.ItemPage)):
                inverse_ppage = pywikibot.PropertyPage(self.repo, inverse_prop)
                if inverse_ppage.type != 'wikibase-item':
                    raise ValueError("{} does not have 'wikibase-item' type"
                                     .format(inverse_ppage))
                inverse_claim = inverse_ppage.newClaim()
                inverse_claim.setTarget(item)
                self.user_add_claim_unless_exists(
                    target, inverse_claim, exists_arg, site, pywikibot.info)

            # Stop after the first match if not supposed to add
            # multiple values
            if not do_multi:
                break

            # Update exists_arg, so we can add more values
            if added:
                exists_arg.add('p')

    def handle_wikibase_item(self, value: str,
                             site: pywikibot.site.BaseSite,
                             item: pywikibot.page.ItemPage,
                             field: str) -> Iterator[pywikibot.ItemPage]:
        """Handle 'wikibase-item' claim type.

        .. versionadded:: 7.5
        """
        value = value.replace('{{!}}', '|')
        prop, options = self.fields[field]
        matched = False

        # Try to extract a valid page
        for match in pywikibot.link_regex.finditer(value):
            matched = True
            link_text = match[1]
            linked_item = self.template_link_target(item, site, link_text)
            if linked_item:
                yield linked_item

        if matched:
            return

        if not self._get_option_with_fallback(options, 'islink'):
            pywikibot.info(
                '{} field {} value "{}" is not a wikilink. Skipping.'
                .format(prop, field, value))
            return

        linked_item = self.template_link_target(item, site, value)
        if linked_item:
            yield linked_item

    def handle_time(self, value: str,
                    site: pywikibot.site.BaseSite,
                    *args) -> Iterator[WbTime]:
        """Handle 'time' claim type.

        .. versionadded:: 7.5
        """
        value = value.replace('{{!}}', '|')
        value = value.replace('&nbsp;', ' ')
        value = re.sub('</?sup>', '', value)

        # Some wikis format dates using wikilinks. We construct
        # all possible texts, e.g., "[[A|B]] of [[C]]" becomes
        # "A of C" and "B of C", and parse them using the API.
        # If the result is same for all the values, we import
        # the value.
        to_parse = {''}
        prev_end = 0
        for match in pywikibot.link_regex.finditer(value):
            start, end = match.span()
            since_prev_match = value[prev_end:start]

            title = match['title'].strip()
            text = match[2]
            if text:
                text = text[1:].strip()  # remove '|'

            new_to_parse = set()
            for fragment in to_parse:
                fragment += since_prev_match
                new_to_parse.add(fragment + title)
                if text:
                    new_to_parse.add(fragment + text)

            to_parse = new_to_parse
            prev_end = end

        rest = value[prev_end:]
        to_parse = [text + rest for text in to_parse]

        try:
            result = self.repo.parsevalue('time', to_parse, language=site.lang)
        except (APIError, ValueError):
            return

        out = None
        for data in result:
            if out is None:
                out = data
            elif out != data:
                pywikibot.info(f'Found ambiguous date: "{value}"')
                return

        yield WbTime.fromWikibase(out, self.repo)

    @staticmethod
    def handle_string(value, *args) -> Iterator[str]:
        """Handle 'string' and 'external-id' claim type.

        .. versionadded:: 7.5
        """
        yield value.strip()

    handle_external_id = handle_string

    def handle_url(self, value, *args) -> Iterator[str]:
        """Handle 'url' claim type.

        .. versionadded:: 7.5
        """
        for match in self.linkR.finditer(value):
            yield match['url']

    @staticmethod
    def handle_commonsmedia(value, site,
                            *args) -> Iterator[pywikibot.FilePage]:
        """Handle 'commonsMedia' claim type.

        .. versionadded:: 7.5
        """
        repo = site.image_repository()
        image = pywikibot.FilePage(repo, value)
        if image.isRedirectPage():
            image = pywikibot.FilePage(image.getRedirectTarget())

        if not image.exists():
            pywikibot.info("{} doesn't exist so it cannot be linked"
                           .format(image.title(as_link=True)))
            return

        yield image


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    template_title = None

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    gen = pg.GeneratorFactory()

    current_args = []
    fields = {}
    options = {}
    for arg in local_args:
        opt, _, value = arg.partition(':')
        if opt == '-template':
            template_title = value or pywikibot.input(
                'Please enter the template to work on:')
        elif opt == '-confirm':
            options['always'] = False
        elif arg.startswith('-create'):
            options['create'] = True
        elif gen.handle_arg(arg):
            if arg.startswith('-transcludes:'):
                template_title = value
        else:
            optional = opt.startswith('-')
            complete = len(current_args) == 3
            if optional:
                needs_second = len(current_args) == 1
                if needs_second:
                    break  # will stop below

                arg = opt[1:]
                if len(current_args) == 0:
                    assert not fields
                    options[arg] = value or True
                else:
                    assert complete
                    current_args[2][arg] = value or True
            else:
                if complete:
                    handler = PropertyOptionHandler(**current_args[2])
                    fields[current_args[0]] = (current_args[1], handler)
                    del current_args[:]
                current_args.append(arg)
                if len(current_args) == 2:
                    current_args.append({})

    # handle leftover
    if len(current_args) == 3:
        handler = PropertyOptionHandler(**current_args[2])
        fields[current_args[0]] = (current_args[1], handler)
    elif len(current_args) == 1:
        pywikibot.error('Incomplete command line param-property pair.')
        return

    if not template_title:
        pywikibot.error(
            'Please specify either -template or -transcludes argument')
        return

    if not fields:
        pywikibot.error('No template parameters to harvest specified.')
        return

    if not gen.gens:
        gen.handle_arg('-transcludes:' + template_title)
    generator = gen.getCombinedGenerator(preload=True)

    bot = HarvestRobot(template_title, fields, generator=generator, **options)
    bot.run()


if __name__ == '__main__':
    main()
