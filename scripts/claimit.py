#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
A script that adds claims to Wikidata items based on categories.

------------------------------------------------------------------------------

Usage:

python claimit.py [pagegenerators] P1 Q2 P123 Q456

You can use any typical pagegenerator to provide with a list of pages.
Then list the property-->target pairs to add.

------------------------------------------------------------------------------

For geographic coordinates:

python claimit.py [pagegenerators] P625 [lat-dec],[long-dec],[prec]

[lat-dec] and [long-dec] represent the latitude and longitude respectively,
and [prec] represents the precision. All values are in decimal degrees,
not DMS. If [prec] is omitted, the default precision is 0.0001 degrees.

Example:

python claimit.py [pagegenerators] P625 -23.3991,-52.0910,0.0001

------------------------------------------------------------------------------

By default, claimit.py does not add a claim if one with the same property
already exists on the page. To override this behavior, use the 'exists' option:

python claimit.py [pagegenerators] P246 "string example" -exists:p

Suppose the claim you want to add has the same property as an existing claim
and the "-exists:p" argument is used. Now, claimit.py will not add the claim
if it has the same target, sources, and/or qualifiers as the existing claim.
To override this behavior, add 't' (target), 's' (sources), or 'q' (qualifiers)
to the 'exists' argument.

For instance, to add the claim to each page even if one with the same
property, target, and qualifiers already exists:

python claimit.py [pagegenerators] P246 "string example" -exists:ptq

Note that the ordering of the letters in the 'exists' argument does not matter,
but 'p' must be included.

"""
#
# (C) Legoktm, 2013
# (C) Pywikibot team, 2013-2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

import pywikibot
from pywikibot import pagegenerators, WikidataBot

# This is required for the text that is shown when you run this script
# with the parameter -help or without parameters.
docuReplacements = {
    '&params;': pagegenerators.parameterHelp,
}


class ClaimRobot(WikidataBot):

    """A bot to add Wikidata claims."""

    def __init__(self, generator, claims, exists_arg=''):
        """
        Constructor.

        Arguments:
            * generator    - A generator that yields Page objects.
            * claims       - A list of wikidata claims
            * exists_arg   - String specifying how to handle duplicate claims

        """
        super(ClaimRobot, self).__init__(use_from_page=None)
        self.generator = generator
        self.claims = claims
        self.exists_arg = exists_arg
        self.cacheSources()
        if self.exists_arg:
            pywikibot.output('\'exists\' argument set to \'%s\'' % self.exists_arg)

    def treat(self, page, item):
        """Treat each page."""
        self.current_page = page

        if item:
            for claim in self.claims:
                skip = False
                # If claim with same property already exists...
                if claim.getID() in item.claims:
                    if self.exists_arg is None or 'p' not in self.exists_arg:
                        pywikibot.log('Skipping %s because claim with same property already exists' % (claim.getID(),))
                        pywikibot.log('Use the -exists:p option to override this behavior')
                        skip = True
                    else:
                        existing_claims = item.claims[claim.getID()]  # Existing claims on page of same property
                        for existing in existing_claims:
                            skip = True  # Default value
                            # If some attribute of the claim being added matches some attribute in an existing claim
                            # of the same property, skip the claim, unless the 'exists' argument overrides it.
                            if claim.getTarget() == existing.getTarget() and 't' not in self.exists_arg:
                                pywikibot.log('Skipping %s because claim with same target already exists' % (claim.getID(),))
                                pywikibot.log('Append \'t\' to the -exists argument to override this behavior')
                                break
                            if listsEqual(claim.getSources(), existing.getSources()) and 's' not in self.exists_arg:
                                pywikibot.log('Skipping %s because claim with same sources already exists' % (claim.getID(),))
                                pywikibot.log('Append \'s\' to the -exists argument to override this behavior')
                                break
                            if listsEqual(claim.qualifiers, existing.qualifiers) and 'q' not in self.exists_arg:
                                pywikibot.log('Skipping %s because claim with same qualifiers already exists' % (claim.getID(),))
                                pywikibot.log('Append \'q\' to the -exists argument to override this behavior')
                                break
                            skip = False
                if not skip:
                    pywikibot.output('Adding %s --> %s'
                                     % (claim.getID(), claim.getTarget()))
                    item.addClaim(claim)
                    # A generator might yield pages from multiple languages
                    source = self.getSource(page.site)
                    if source:
                        claim.addSource(source, bot=True)
                    # TODO FIXME: We need to check that we aren't adding a
                    # duplicate


def listsEqual(list1, list2):
    """
    Return true if the lists are probably equal, ignoring order.

    Works for lists of unhashable items (like dictionaries).
    """
    if len(list1) != len(list2):
        return False
    if sorted(list1) != sorted(list2):
        return False
    for item in list1:
        if item not in list2:
            return False
    return True


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    exists_arg = ''
    commandline_claims = list()

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    gen = pagegenerators.GeneratorFactory()

    for arg in local_args:
        # Handle args specifying how to handle duplicate claims
        if arg.startswith('-exists:'):
            exists_arg = arg.split(':')[1].strip('"')
            continue
        # Handle page generator args
        if gen.handleArg(arg):
            continue
        commandline_claims.append(arg)
    if len(commandline_claims) % 2:
        raise ValueError  # or something.

    claims = list()
    repo = pywikibot.Site().data_repository()
    for i in range(0, len(commandline_claims), 2):
        claim = pywikibot.Claim(repo, commandline_claims[i])
        if claim.type == 'wikibase-item':
            target = pywikibot.ItemPage(repo, commandline_claims[i + 1])
        elif claim.type == 'string':
            target = commandline_claims[i + 1]
        elif claim.type == 'globe-coordinate':
            coord_args = [float(c) for c in commandline_claims[i + 1].split(',')]
            if len(coord_args) >= 3:
                precision = coord_args[2]
            else:
                precision = 0.0001  # Default value (~10 m at equator)
            target = pywikibot.Coordinate(coord_args[0], coord_args[1], precision=precision)
        else:
            raise NotImplementedError(
                "%s datatype is not yet supported by claimit.py"
                % claim.type)
        claim.setTarget(target)
        claims.append(claim)

    generator = gen.getCombinedGenerator()
    if not generator:
        # show help text from the top of this file
        pywikibot.showHelp()
        return

    bot = ClaimRobot(generator, claims, exists_arg)
    bot.run()

if __name__ == "__main__":
    main()
