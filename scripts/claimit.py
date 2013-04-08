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


def main():
    gen = pagegenerators.GeneratorFactory()
    claims = list()
    for arg in pywikibot.handleArgs():
        if gen.handleArg(arg):
            continue
        claims.append(arg)
    if len(claims) % 2 != 0:
        raise ValueError  # or something.
    real_claims = list()
    c = 0
    while c != len(claims):
        claim = pywikibot.Claim(repo, claims[c])
        claim.setTarget(pywikibot.ItemPage(repo, claims[c+1]))
        real_claims.append(claim)
        c += 2

    generator = gen.getCombinedGenerator()

    for page in generator:
        item = pywikibot.ItemPage.fromPage(page)
        pywikibot.output('Processing %s' % page)
        if not item.exists():
            pywikibot.output('%s doesn\'t have a wikidata item :(' % page)
            #TODO FIXME: We should provide an option to create the page
            continue

        for claim in real_claims:
            pywikibot.output('Adding %s --> %s' % (claim.getID(), claim.getTarget().getID()))
            item.addClaim(claim)
            #TODO FIXME: We should add a source for each claim that is added
            #TODO FIXME: We need to check that we aren't adding a duplicate


