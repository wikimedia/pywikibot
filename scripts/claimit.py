#!/usr/bin/python
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

class ClaimRobot:
    """
    A bot to add Wikidata claims
    """
    def __init__(self, generator, claims):
        """
        Arguments:
            * generator    - A generator that yields Page objects.
            * claims       - A list of wikidata claims

        """
        self.generator = generator
        self.claims = claims
        self.repo = pywikibot.Site().data_repository()
        self.source = None
        self.setSource(pywikibot.Site().language())
    
    def setSource(self, lang):
        '''
        Get the source
        '''
        source_values = {'en': pywikibot.ItemPage(self.repo, 'Q328'),
                         'sv': pywikibot.ItemPage(self.repo, 'Q169514'),
                         'de': pywikibot.ItemPage(self.repo, 'Q48183'),
                         'it': pywikibot.ItemPage(self.repo, 'Q11920'),
                         'no': pywikibot.ItemPage(self.repo, 'Q191769'),
                         'ar': pywikibot.ItemPage(self.repo, 'Q199700'),
                         'es': pywikibot.ItemPage(self.repo, 'Q8449'),
                         'pl': pywikibot.ItemPage(self.repo, 'Q1551807'),
                         'ca': pywikibot.ItemPage(self.repo, 'Q199693'),
                         'fr': pywikibot.ItemPage(self.repo, 'Q8447'),
                         'nl': pywikibot.ItemPage(self.repo, 'Q10000'),
                         'pt': pywikibot.ItemPage(self.repo, 'Q11921'),
                         'ru': pywikibot.ItemPage(self.repo, 'Q206855'),
                         'vi': pywikibot.ItemPage(self.repo, 'Q200180'),
                         'be': pywikibot.ItemPage(self.repo, 'Q877583'),
                         'uk': pywikibot.ItemPage(self.repo, 'Q199698'),
                         'tr': pywikibot.ItemPage(self.repo, 'Q58255'),
                 }  # TODO: This should include all projects
        
        if lang in source_values:
            self.source = pywikibot.Claim(self.repo, 'p143')
            self.source.setTarget(source_values.get(lang))

    def run(self):
        """
        Starts the robot.
        """
        for page in self.generator:
            item = pywikibot.ItemPage.fromPage(page)
            pywikibot.output('Processing %s' % page)
            if not item.exists():
                pywikibot.output('%s doesn\'t have a wikidata item :(' % page)
                #TODO FIXME: We should provide an option to create the page
            else:
                for claim in self.claims:
                    if claim.getID() in item.get().get('claims'):
                        pywikibot.output(u'A claim for %s already exists. Skipping' % (claim.getID(),))
                        #TODO FIXME: This is a very crude way of dupe checking
                    else:
                        pywikibot.output('Adding %s --> %s' % (claim.getID(), claim.getTarget().getID()))
                        item.addClaim(claim)
                        if self.source:
                            claim.addSource(self.source, bot=True)
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

    repo = pywikibot.Site().data_repository()

    for i in xrange (0, len(commandline_claims), 2):
        claim = pywikibot.Claim(repo, commandline_claims[i])
        claim.setTarget(pywikibot.ItemPage(repo, commandline_claims[i+1]))
        claims.append(claim)

    generator = gen.getCombinedGenerator()
    if not generator:
        # FIXME: Should throw some help
        return
    
    bot = ClaimRobot(generator, claims)
    bot.run()

if __name__ == "__main__":
    main()
