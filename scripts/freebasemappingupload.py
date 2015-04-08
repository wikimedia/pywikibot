#!/usr/bin/python
# -*- coding: utf-8    -*-
"""
Script to upload the mappings of Freebase to Wikidata.

Can be easily adapted to upload other String identifiers as well

This bot needs the dump from
https://developers.google.com/freebase/data#freebase-wikidata-mappings

The script takes a single parameter:

-filename: the filename to read the freebase-wikidata mappings from;
           default: fb2w.nt.gz
"""
#
# (C) Denny Vrandecic, 2013
# (C) Pywikibot team, 2013-2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

import gzip
import os
import sys

import pywikibot


class FreebaseMapperRobot:

    """Freebase Mapping bot."""

    def __init__(self, filename):
        self.repo = pywikibot.Site('wikidata', 'wikidata').data_repository()
        self.filename = filename
        if not os.path.exists(self.filename):
            pywikibot.output('Cannot find %s. Try providing the absolute path.'
                             % self.filename)
            sys.exit(1)

    def run(self):
        # Set up some items we will use a lot.
        self.claim = pywikibot.Claim(self.repo, 'P646')  # freebase mapping
        # And sources!
        self.statedin = pywikibot.Claim(self.repo, 'P248')  # stated in
        freebasedumpitem = pywikibot.ItemPage(self.repo, 'Q15241312')  # Freebase data dump
        self.statedin.setTarget(freebasedumpitem)
        self.dateofpub = pywikibot.Claim(self.repo, 'P577')  # date of publication
        oct28 = pywikibot.WbTime(site=self.repo, year=2013, month=10, day=28, precision='day')
        self.dateofpub.setTarget(oct28)

        for line in gzip.open(self.filename):
            self.processLine(line.strip())

    def processLine(self, line):
        if not line or line.startswith('#'):
            return
        mid, sameas, qid, dot = line.split()
        if sameas != '<https://www.w3.org/2002/07/owl#sameAs>':
            return
        if dot != '.':
            return
        if not mid.startswith('<https://rdf.freebase.com/ns/m'):
            return
        mid = '/m/' + mid[30:-1]
        if not qid.startswith('<https://www.wikidata.org/entity/Q'):
            return
        qid = 'Q' + qid[33:-1]
        data = pywikibot.ItemPage(self.repo, qid)
        data.get()
        if not data.labels:
            label = ''
        elif 'en' in data.labels:
            label = data.labels['en']
        else:
            # Just pick up the first label
            label = list(data.labels.values())[0]
        pywikibot.output('Parsed: %s <--> %s' % (qid, mid))
        pywikibot.output('%s is %s' % (data.getID(), label))
        if data.claims and 'P646' in data.claims:
            # We assume that there is only one claim.
            # If there are multiple ones, our logs might be wrong
            # but the constraint value reports will catch them
            if mid != data.claims['P646'][0].getTarget():
                pywikibot.output('Mismatch: expected %s, has %s instead'
                                 % (mid, data.claims['P646'][0].getTarget()))
            else:
                pywikibot.output('Already has mid set, is consistent.')
        else:
            # No claim set, lets add it.
            pywikibot.output('Going to add a new claim.')
            self.claim.setTarget(mid)
            data.addClaim(self.claim)
            self.claim.addSources([self.statedin, self.dateofpub])
            pywikibot.output('Claim added!')


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    filename = 'fb2w.nt.gz'  # Default filename
    for arg in pywikibot.handle_args(args):
        if arg.startswith('-filename'):
            filename = arg[11:]
    bot = FreebaseMapperRobot(filename)
    bot.run()

if __name__ == '__main__':
    main()
