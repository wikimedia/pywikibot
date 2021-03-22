#!/usr/bin/python
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

Examples
--------

This will try to import existing images from "image" parameter of "Infobox
person" on English Wikipedia as Wikidata property "P18" (image):

    python pwb.py harvest_template -lang:en -family:wikipedia -namespace:0 \
        -template:"Infobox person" image P18

This will behave the same as the previous example and also try to import
[[links]] from "birth_place" parameter of the same template as Wikidata
property "P19" (place of birth):

    python pwb.py harvest_template -lang:en -family:wikipedia -namespace:0 \
        -template:"Infobox person" image P18 birth_place P19

This will import both "birth_place" and "death_place" params with -islink
modifier, ie. the bot will try to import values, even if it doesn't find
a [[link]]:

    python pwb.py harvest_template -lang:en -family:wikipedia -namespace:0 \
        -template:"Infobox person" -islink birth_place P19 death_place P20

This will do the same but only "birth_place" can be imported without a link:

    python pwb.py harvest_template -lang:en -family:wikipedia -namespace:0 \
        -template:"Infobox person" birth_place P19 -islink death_place P20

This will import an occupation from "occupation" parameter of "Infobox
person" on English Wikipedia as Wikidata property "P106" (occupation). The
page won't be skipped if the item already has that property but there is
not the new value:

    python pwb.py harvest_template -lang:en -family:wikipedia -namespace:0 \
        -template:"Infobox person" occupation P106 -exists:p

This will import band members from the "current_members" parameter of "Infobox
musical artist" on English Wikipedia as Wikidata property "P527" (has
part). This will only extract multiple band members if each is linked, and
will not add duplicate claims for the same member:

    python pwb.py harvest_template -lang:en -family:wikipedia -namespace:0 \
        -template:"Infobox musical artist" current_members P527 -exists:p \
        -multi
"""
#
# (C) Pywikibot team, 2013-2021
#
# Distributed under the terms of MIT License.
#
import signal
import sys
from typing import Any, Optional

import pywikibot
from pywikibot import pagegenerators as pg
from pywikibot import textlib
from pywikibot.backports import List
from pywikibot.bot import OptionHandler, WikidataBot
from pywikibot.exceptions import InvalidTitleError, NoPageError


willstop = False


def _signal_handler(signal, frame) -> None:
    global willstop
    if not willstop:
        willstop = True
        pywikibot.output('Received ctrl-c. Finishing current item; '
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
    }


class HarvestRobot(WikidataBot):

    """A bot to add Wikidata claims."""

    def __init__(self, generator, template_title, fields, **kwargs) -> None:
        """
        Initializer.

        :param generator: A generator that yields Page objects
        :type generator: iterator
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
        """
        self.available_options.update({
            'always': True,
            'create': False,
            'exists': '',
            'islink': False,
            'multi': False,
        })
        super().__init__(**kwargs)
        self.generator = generator
        # TODO: Make it a list including the redirects to the template
        self.fields = {}
        for key, value in fields.items():
            if isinstance(value, tuple):
                self.fields[key] = value
            else:  # backwards compatibility
                self.fields[key] = (value, PropertyOptionHandler())
        self.cacheSources()
        template_title = template_title.replace('_', ' ')
        self.templateTitles = self.getTemplateSynonyms(template_title)
        self.linkR = textlib.compileLinkR()
        self.create_missing_item = self.opt.create

    def getTemplateSynonyms(self, title) -> List[str]:
        """Fetch redirects of the title, so we can check against them."""
        temp = pywikibot.Page(pywikibot.Site(), title, ns=10)
        if not temp.exists():
            sys.exit('Template {} does not exist.'.format(temp.title()))

        # Put some output here since it can take a while
        pywikibot.output('Finding redirects...')
        if temp.isRedirectPage():
            temp = temp.getRedirectTarget()
        titles = [page.title(with_ns=False)
                  for page in temp.getReferences(filter_redirects=True,
                                                 namespaces=[10],
                                                 follow_redirects=False)]
        titles.append(temp.title(with_ns=False))
        return titles

    def _template_link_target(self, item, link_text
                              ) -> Optional[pywikibot.ItemPage]:
        link = pywikibot.Link(link_text)
        linked_page = pywikibot.Page(link)
        try:
            exists = linked_page.exists()
        except InvalidTitleError:
            pywikibot.error('"{}" is not a valid title so it cannot be linked.'
                            ' Skipping.'.format(link_text))
            return None

        if not exists:
            pywikibot.output('{} does not exist so it cannot be linked. '
                             'Skipping.'.format(linked_page))
            return None

        if linked_page.isRedirectPage():
            linked_page = linked_page.getRedirectTarget()

        try:
            linked_item = pywikibot.ItemPage.fromPage(linked_page)
        except NoPageError:
            linked_item = None

        if not linked_item or not linked_item.exists():
            pywikibot.output('{} does not have a wikidata item to link with. '
                             'Skipping.'.format(linked_page))
            return None

        if linked_item.title() == item.title():
            pywikibot.output('{} links to itself. Skipping.'
                             .format(linked_page))
            return None

        return linked_item

    def _get_option_with_fallback(self, handler, option) -> Any:
        """
        Compare bot's (global) and provided (local) options.

        :see: :py:obj:`OptionHandler`
        """
        default = self.opt[option]
        local = handler.opt[option]
        if isinstance(default, bool) and isinstance(local, bool):
            return default is not local
        return local or default

    def treat_page_and_item(self, page, item) -> None:
        """Process a single page/item."""
        if willstop:
            raise KeyboardInterrupt

        templates = page.raw_extracted_templates
        for (template, fielddict) in templates:
            # Clean up template
            try:
                template = pywikibot.Page(page.site, template,
                                          ns=10).title(with_ns=False)
            except InvalidTitleError:
                pywikibot.error(
                    "Failed parsing template; '{}' should be "
                    'the template name.'.format(template))
                continue

            if template not in self.templateTitles:
                continue
            # We found the template we were looking for
            for field, value in fielddict.items():
                field = field.strip()
                # todo: extend the list of tags to ignore
                value = textlib.removeDisabledParts(
                    # todo: eventually we may want to import the references
                    value, tags=['ref'], site=page.site).strip()
                if not field or not value:
                    continue

                if field not in self.fields:
                    continue

                # This field contains something useful for us
                prop, options = self.fields[field]
                claim = pywikibot.Claim(self.repo, prop)
                exists_arg = self._get_option_with_fallback(options, 'exists')
                if claim.type == 'wikibase-item':
                    do_multi = self._get_option_with_fallback(
                        options, 'multi')
                    matched = False
                    # Try to extract a valid page
                    for match in pywikibot.link_regex.finditer(value):
                        matched = True
                        link_text = match.group(1)
                        linked_item = self._template_link_target(
                            item, link_text)
                        added = False
                        if linked_item:
                            claim.setTarget(linked_item)
                            added = self.user_add_claim_unless_exists(
                                item, claim, exists_arg, page.site,
                                pywikibot.output)
                            claim = pywikibot.Claim(self.repo, prop)
                        # stop after the first match if not supposed to add
                        # multiple values
                        if not do_multi:
                            break
                        # update exists_arg, so we can add more values
                        if 'p' not in exists_arg and added:
                            exists_arg += 'p'

                    if matched:
                        continue

                    if not self._get_option_with_fallback(options, 'islink'):
                        pywikibot.output(
                            '{} field {} value {} is not a wikilink. Skipping.'
                            .format(claim.getID(), field, value))
                        continue

                    linked_item = self._template_link_target(item, value)
                    if not linked_item:
                        continue

                    claim.setTarget(linked_item)
                elif claim.type in ('string', 'external-id'):
                    claim.setTarget(value.strip())
                elif claim.type == 'url':
                    match = self.linkR.search(value)
                    if not match:
                        continue
                    claim.setTarget(match.group('url'))
                elif claim.type == 'commonsMedia':
                    commonssite = pywikibot.Site('commons', 'commons')
                    imagelink = pywikibot.Link(
                        value, source=commonssite, default_namespace=6)
                    image = pywikibot.FilePage(imagelink)
                    if image.isRedirectPage():
                        image = pywikibot.FilePage(image.getRedirectTarget())
                    if not image.exists():
                        pywikibot.output(
                            "{} doesn't exist. I can't link to it"
                            .format(image.title(as_link=True)))
                        continue
                    claim.setTarget(image)
                else:
                    pywikibot.output('{} is not a supported datatype.'
                                     .format(claim.type))
                    continue

                # A generator might yield pages from multiple sites
                self.user_add_claim_unless_exists(
                    item, claim, exists_arg, page.site, pywikibot.output)


def main(*args) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    :type args: str
    """
    template_title = None

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    gen = pg.GeneratorFactory()

    current_args = []
    fields = {}
    options = {}
    for arg in local_args:
        if arg.startswith('-template'):
            if len(arg) == 9:
                template_title = pywikibot.input(
                    'Please enter the template to work on:')
            else:
                template_title = arg[10:]
        elif arg.startswith('-create'):
            options['create'] = True
        elif gen.handle_arg(arg):
            if arg.startswith('-transcludes:'):
                template_title = arg[13:]
        else:
            optional = arg.startswith('-')
            complete = len(current_args) == 3
            if optional:
                needs_second = len(current_args) == 1
                if needs_second:
                    break  # will stop below

                arg, sep, value = arg[1:].partition(':')
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

    generator = gen.getCombinedGenerator(preload=True)
    if not generator:
        gen.handle_arg('-transcludes:' + template_title)
        generator = gen.getCombinedGenerator(preload=True)

    bot = HarvestRobot(generator, template_title, fields, **options)
    bot.run()


if __name__ == '__main__':
    main()
