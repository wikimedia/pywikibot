# -*- coding: utf-8 -*-
"""
Copyright (C) 2013 Legoktm
Copyright (C) 2013 Pywikipediabot team

Distributed under the MIT License

Usage:

python claimit.py [pagegenerators] P1 Q2 P123 Q456

You can use any typical pagegenerator to provide with a list of pages

Then list the property-->target pairs to add.
"""
import pywikibot
from pywikibot import pagegenerators
repo = pywikibot.Site().data_repository()

source_values = {'en': pywikibot.ItemPage(repo, 'Q328'),
                 'sv': pywikibot.ItemPage(repo, 'Q169514'),
                 'de': pywikibot.ItemPage(repo, 'Q48183'),
                 'it': pywikibot.ItemPage(repo, 'Q11920'),
                 'no': pywikibot.ItemPage(repo, 'Q191769'),
                 'ar': pywikibot.ItemPage(repo, 'Q199700'),
                 'es': pywikibot.ItemPage(repo, 'Q8449'),
                 'pl': pywikibot.ItemPage(repo, 'Q1551807'),
                 'ca': pywikibot.ItemPage(repo, 'Q199693'),
                 'fr': pywikibot.ItemPage(repo, 'Q8447'),
                 'nl': pywikibot.ItemPage(repo, 'Q10000'),
                 'pt': pywikibot.ItemPage(repo, 'Q11921'),
                 'ru': pywikibot.ItemPage(repo, 'Q206855'),
                 'vi': pywikibot.ItemPage(repo, 'Q200180'),
                 'be': pywikibot.ItemPage(repo, 'Q877583'),
                 'uk': pywikibot.ItemPage(repo, 'Q199698'),
                 'tr': pywikibot.ItemPage(repo, 'Q58255'),
                 }  # TODO: This should include all projects

imported_from = pywikibot.Claim(repo, 'p143')
source = source_values.get(pywikibot.Site().language(), None)
if source:
    imported_from.setTarget(source)

def addClaims(page, claims):
    '''
    The function will add the claims to the wikibase page
    '''
    item = pywikibot.ItemPage.fromPage(page)
    pywikibot.output('Processing %s' % page)
    if not item.exists():
        pywikibot.output('%s doesn\'t have a wikidata item :(' % page)
        #TODO FIXME: We should provide an option to create the page
        return False

    for claim in claims:
        if claim.getID() in item.get().get('claims'):
            pywikibot.output(u'A claim for %s already exists. Skipping' % (claim.getID(),))
            #TODO FIXME: This is a very crude way of dupe checking
        else:
            pywikibot.output('Adding %s --> %s' % (claim.getID(), claim.getTarget().getID()))
            item.addClaim(claim)
            if source:
                claim.addSource(imported_from, bot=True)
            #TODO FIXME: We need to check that we aren't adding a duplicate


def main():
    gen = pagegenerators.GeneratorFactory()
    commandline_claims = list()
    for arg in pywikibot.handleArgs():
        if gen.handleArg(arg):
            continue
        commandline_claims.append(arg)
    if len(commandline_claims) % 2:
        raise ValueError  # or something.
    claims = list()

    for i in xrange (0, len(commandline_claims), 2):
        claim = pywikibot.Claim(repo, commandline_claims[i])
        claim.setTarget(pywikibot.ItemPage(repo, commandline_claims[i+1]))
        claims.append(claim)

    generator = gen.getCombinedGenerator()

    if generator:
        for page in generator:
            addClaims(page, claims)

if __name__ == "__main__":
    main()
