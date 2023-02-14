#!/usr/bin/env python3
"""
A script that adds claims to Wikidata items based on a list of pages.

These command line parameters can be used to specify which pages to work on:

&params;

Usage:

    python pwb.py claimit [pagegenerators] P1 Q2 P123 Q456

You can use any typical pagegenerator (like categories) to provide with a
list of pages. Then list the property-->target pairs to add.

For geographic coordinates:

    python pwb.py claimit [pagegenerators] P625 [lat-dec],[long-dec],[prec]

[lat-dec] and [long-dec] represent the latitude and longitude respectively,
and [prec] represents the precision. All values are in decimal degrees,
not DMS. If [prec] is omitted, the default precision is 0.0001 degrees.

Example:

    python pwb.py claimit [pagegenerators] P625 -23.3991,-52.0910,0.0001

By default, claimit.py does not add a claim if one with the same property
already exists on the page. To override this behavior, use the 'exists' option:

    python pwb.py claimit [pagegenerators] P246 "string example" -exists:p

Suppose the claim you want to add has the same property as an existing claim
and the "-exists:p" argument is used. Now, claimit.py will not add the claim
if it has the same target, source, and/or the existing claim has qualifiers.
To override this behavior, add 't' (target), 's' (sources), or 'q' (qualifiers)
to the 'exists' argument.

For instance, to add the claim to each page even if one with the same
property and target and some qualifiers already exists:

    python pwb.py claimit [pagegenerators] P246 "string example" -exists:ptq

Note that the ordering of the letters in the 'exists' argument does not matter,
but 'p' must be included.

"""
#
# (C) Pywikibot team, 2013-2022
#
# Distributed under the terms of the MIT license.
#
import pywikibot
from pywikibot import WikidataBot, pagegenerators
from pywikibot.backports import removeprefix
from pywikibot.tools.itertools import itergroup


# This is required for the text that is shown when you run this script
# with the parameter -help or without parameters.
docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816


class ClaimRobot(WikidataBot):

    """A bot to add Wikidata claims."""

    use_from_page = None

    def __init__(self, claims, exists_arg: str = '', **kwargs) -> None:
        """Initializer.

        :param claims: A list of wikidata claims
        :type claims: list
        :param exists_arg: String specifying how to handle duplicate claims
        """
        self.available_options['always'] = True
        super().__init__(**kwargs)
        self.claims = claims
        self.exists_arg = ''.join(x for x in exists_arg.lower() if x in 'pqst')
        self.cacheSources()
        if self.exists_arg:
            pywikibot.info(f"'exists' argument set to '{self.exists_arg}'")

    def treat_page_and_item(self, page, item) -> None:
        """Treat each page.

        :param page: The page to update and change
        :type page: pywikibot.page.BasePage
        :param item: The item to treat
        :type item: pywikibot.page.ItemPage
        """
        for claim in self.claims:
            # The generator might yield pages from multiple sites
            site = page.site if page is not None else None
            self.user_add_claim_unless_exists(
                item, claim.copy(), self.exists_arg, site)


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    exists_arg = ''
    commandline_claims = []

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    gen = pagegenerators.GeneratorFactory()

    for arg in local_args:
        # Handle args specifying how to handle duplicate claims
        if arg.startswith('-exists:'):
            exists_arg = removeprefix(arg, '-exists:')
            continue
        # Handle page generator args
        if gen.handle_arg(arg):
            continue
        commandline_claims.append(arg)
    if len(commandline_claims) % 2:
        pywikibot.error('Incomplete command line property-value pair.')
        return

    claims = []
    repo = pywikibot.Site().data_repository()
    for property_id, target_str in itergroup(commandline_claims, 2):
        claim = pywikibot.Claim(repo, property_id)
        if claim.type == 'wikibase-item':
            target = pywikibot.ItemPage(repo, target_str)
        elif claim.type == 'string':
            target = target_str
        elif claim.type == 'globe-coordinate':
            coord_args = [
                float(c) for c in target_str.split(',')]
            if len(coord_args) >= 3:
                precision = coord_args[2]
            else:
                precision = 0.0001  # Default value (~10 m at equator)
            target = pywikibot.Coordinate(
                coord_args[0], coord_args[1], precision=precision)
        else:
            raise NotImplementedError(
                '{} datatype is not yet supported by claimit.py'
                .format(claim.type))
        claim.setTarget(target)
        claims.append(claim)

    generator = gen.getCombinedGenerator()
    if not generator:
        pywikibot.bot.suggest_help(missing_generator=True)
        return

    bot = ClaimRobot(claims, exists_arg, generator=generator)
    bot.run()


if __name__ == '__main__':
    main()
