#!/usr/bin/python
"""Bot to find all pages on the wiki with mixed latin and cyrilic alphabets."""
#
# (C) Pywikibot team, 2006-2021
#
# Distributed under the terms of the MIT license.
#
import codecs
import os
import re
import sys
from itertools import chain, combinations
from string import ascii_letters

import pywikibot
from pywikibot import i18n
from pywikibot.data import api
from pywikibot.exceptions import LockedPageError, PageSaveRelatedError
from pywikibot.tools import first_lower, first_upper, formatter
from scripts.category import CategoryMoveRobot as CategoryMoveBot


class CaseChecker:

    """Case checker."""

    # These words are always in one language, even though they could be typed
    # in both
    alwaysInLocal = ['СССР', 'Как', 'как']
    alwaysInLatin = ['II', 'III']

    localUpperLtr = 'ЁІЇЎАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯҐ'
    localLowerLtr = 'ёіїўабвгдежзийклмнопрстуфхцчшщъыьэюяґ'
    localLtr = localUpperLtr + localLowerLtr

    localSuspects = 'АВЕКМНОРСТХІЁЇаеорсухіёї'
    latinSuspects = 'ABEKMHOPCTXIËÏaeopcyxiëï'

    # possibly try to fix one character mistypes in an alternative keyboard
    # layout
    localKeyboard = 'йцукенгшщзфывапролдячсмить'
    latinKeyboard = 'qwertyuiopasdfghjklzxcvbnm'

    romanNumChars = 'IVXLCDM'
    # all letters that may be used as suffixes after roman numbers: "Iый"
    romannumSuffixes = localLowerLtr
    romanNumSfxPtrn = re.compile(
        '[{}]+[{}]+$'.format(romanNumChars, localLowerLtr))

    whitelists = {
        'ru': 'ВП:КЛ/Проверенные',
    }

    lclClrFnt = '<font color=green>'
    latClrFnt = '<font color=brown>'
    suffixClr = '</font>'

    colorFormatLocalColor = '{green}'
    colorFormatLatinColor = '{red}'
    colorFormatSuffix = '{default}'

    wordBreaker = re.compile(r'[ _\-/\|#[\]():]')
    stripChars = ' \t,'

    titles = True
    links = False
    aplimit = None
    apfrom = ''
    title = None
    replace = False
    stopAfter = -1
    wikilog = None
    wikilogfile = 'wikilog.txt'
    failedTitles = 'failedTitles.txt'
    nosuggestions = 'nosuggestions.txt'
    doFailed = False
    titleList = None
    autonomous = False
    namespaces = []
    filterredir = 'nonredirects'

    def handle_args(self):
        """Arg parsing."""
        for arg in pywikibot.handle_args():
            arg, _, value = arg.partition(':')
            if arg == '-from':
                self.apfrom = value or pywikibot.input(
                    'Which page to start from: ')
            elif arg == '-reqsize':
                self.aplimit = int(value)
            elif arg == '-links':
                self.links = True
            elif arg == '-linksonly':
                self.links = True
                self.titles = False
            elif arg == '-replace':
                self.replace = True
            elif arg == '-redir':
                self.filterredir = 'all'
            elif arg == '-redironly':
                self.filterredir = 'redirects'
            elif arg == '-limit':
                self.stopAfter = int(value)
            elif arg in ('-autonomous', '-a'):
                self.autonomous = True
            elif arg == '-ns':
                self.namespaces.append(int(value))
            elif arg == '-wikilog':
                self.wikilogfile = value
            elif arg == '-failedlog':
                self.failedTitles = value
            elif arg == '-failed':
                self.doFailed = True
            else:
                pywikibot.output('Unknown argument {}.'.format(arg))
                pywikibot.show_help()
                sys.exit()

    def __init__(self):
        """Initializer."""
        self.handle_args()
        if not self.namespaces and not self.doFailed:
            if not self.apfrom:
                # 0 should be after templates ns
                self.namespaces = [14, 10, 12, 0]
            else:
                self.namespaces = [0]

        if not self.aplimit:
            self.aplimit = 200 if self.links else 'max'

        if not self.doFailed:
            self.queryParams = {'action': 'query',
                                'generator': 'allpages',
                                'gaplimit': self.aplimit,
                                'gapfilterredir': self.filterredir}
        else:
            self.queryParams = {'action': 'query'}
            if self.apfrom:
                pywikibot.output('Argument "-from" is ignored with "-failed"')

        propParam = 'info'
        if self.links:
            propParam += '|links|categories'
            self.queryParams['pllimit'] = 'max'
            self.queryParams['cllimit'] = 'max'

        self.queryParams['prop'] = propParam

        self.site = pywikibot.Site()

        if len(self.localSuspects) != len(self.latinSuspects):
            raise ValueError('Suspects must be the same size')

        if len(self.localKeyboard) != len(self.latinKeyboard):
            raise ValueError('Keyboard info must be the same size')

        if not os.path.isabs(self.wikilogfile):
            self.wikilogfile = pywikibot.config.datafilepath(self.wikilogfile)

        self.wikilog = self.OpenLogFile(self.wikilogfile)

        if not os.path.isabs(self.failedTitles):
            self.failedTitles = pywikibot.config.datafilepath(
                self.failedTitles)

        if self.doFailed:
            with codecs.open(self.failedTitles, 'r', 'utf-8') as f:
                self.titleList = [self.Page(t) for t in f]
            self.failedTitles += '.failed'

        iterzip = zip(self.localSuspects, self.latinSuspects)
        self.lclToLatDict = {ord(local): latin for local, latin in iterzip}
        self.latToLclDict = {ord(latin): local for local, latin in iterzip}

        if self.localKeyboard is not None:
            iterzip = zip(self.localKeyboard, self.latinKeyboard)
            self.lclToLatKeybDict = {ord(local): latin
                                     for local, latin in iterzip}
            self.latToLclKeybDict = {ord(latin): local
                                     for local, latin in iterzip}
        else:
            self.lclToLatKeybDict = {}
            self.latToLclKeybDict = {}

        badPtrnStr = '([{ascii}][{local}]|[{local}][{ascii}])'.format(
            ascii=ascii_letters, local=self.localLtr)
        self.badWordPtrn = re.compile('[{ascii}{local}]*{bad}[{ascii}{local}]*'
                                      .format(ascii=ascii_letters,
                                              local=self.localLtr,
                                              bad=badPtrnStr))
        self.get_whitelist()

    def get_whitelist(self):
        """Get whitelist."""
        self.knownWords = set()
        self.seenUnresolvedLinks = set()

        # TODO: handle "continue"
        if self.site.code in self.whitelists:
            wlpage = self.whitelists[self.site.code]
            pywikibot.output('Loading whitelist from {}'.format(wlpage))
            wlparams = {
                'action': 'query',
                'prop': 'links',
                'titles': wlpage,
                'redirects': '',
                'indexpageids': '',
                'pllimit': 'max',
            }

            req = api.Request(site=self.site, parameters=wlparams)
            data = req.submit()
            if len(data['query']['pageids']) == 1:
                pageid = data['query']['pageids'][0]
                links = data['query']['pages'][pageid]['links']

                self.knownWords = {nn for n in links
                                   for nn in self.FindBadWords(n['title'])}

            else:
                raise ValueError('The number of pageids is not 1')

            pywikibot.output('Loaded whitelist with {} items'
                             .format(len(self.knownWords)))
            if self.knownWords:
                pywikibot.log('Whitelist: '
                              + ', '.join(self.MakeLink(i, False)
                                          for i in self.knownWords))
        else:
            pywikibot.output(
                'Whitelist is not known for language ' + self.site.code)

    def RunQuery(self, params):
        """API query."""
        while True:
            # Get data
            req = api.Request(**params)
            data = req.submit()

            # Process received data
            yield data

            # Clear any continuations first
            if 'clcontinue' in params:
                del params['clcontinue']
            if 'plcontinue' in params:
                del params['plcontinue']

            if 'query-continue' not in data:
                if 'gapcontinue' in params:
                    del params['gapcontinue']
                break

            qc = data['query-continue']
            # First continue properties only, once done, continue with allpages
            if 'categories' in qc or 'links' in qc:
                if 'categories' in qc:
                    params.update(qc['categories'])
                if 'links' in qc:
                    params.update(qc['links'])
            elif 'allpages' in qc:
                params.update(qc['allpages'])
            else:
                raise ValueError('Unexpected query-continue values: {}'
                                 .format(qc))

    def Run(self):
        """Run the bot."""
        try:
            self.lastLetter = ''

            if not self.doFailed:
                for namespace in self.namespaces:
                    self.currentTitle = None
                    self.queryParams['gapnamespace'] = namespace
                    self.queryParams['gapfrom'] = self.apfrom
                    for data in self.RunQuery(self.queryParams):
                        self.ProcessDataBlock(data)
            else:
                self.currentTitle = None
                batchSize = 10
                for batchStart in range(0, len(self.titleList), batchSize):
                    self.queryParams['titles'] = self.titleList[
                        batchStart:batchStart + batchSize]
                    for data in self.RunQuery(self.queryParams):
                        self.ProcessDataBlock(data)
        except Exception:
            pywikibot.output('Exception at Title = {}, Next = {}'
                             .format(self.currentTitle, self.apfrom))
            pywikibot.exception()
            raise

    def ProcessDataBlock(self, data):
        """Process data block given by RunQuery()."""
        if 'query' not in data or 'pages' not in data['query']:
            return

        firstItem = True
        for page in data['query']['pages'].values():
            printed = False
            title = page['title']
            self.currentTitle = title

            if 'missing' in page:
                continue

            if firstItem:
                if self.lastLetter != title[0]:
                    pywikibot.output('Processing {}\n'.format(title))
                    self.lastLetter = title[0]
                firstItem = False

            if self.titles:
                err = self.ProcessTitle(title)
                if err:
                    changed = False
                    if self.replace:
                        if len(err[1]) == 1:
                            newTitle = err[1][0]
                            editSummary = i18n.twtranslate(
                                self.site, 'casechecker-rename')
                            dst = self.Page(newTitle)

                            if 'redirect' in page:
                                src = self.Page(title)
                                redir = src.getRedirectTarget()
                                redirTitle = redir.title(as_link=True,
                                                         textlink=True)

                                if not dst.exists():
                                    src.move(newTitle, editSummary,
                                             movesubpages=True)
                                    changed = True

                                replErrors = False
                                for p in src.getReferences(
                                        follow_redirects=False):
                                    if p.namespace() == 2:
                                        continue

                                    oldText = p.text
                                    newText = self.ReplaceLink(oldText, title,
                                                               newTitle)
                                    if not self.PutNewPage(
                                        p, newText,
                                            [self.MakeMoveSummary(title,
                                                                  newTitle)]):
                                        replErrors = True

                                if not replErrors:
                                    editSummary = i18n.twtranslate(
                                        self.site,
                                        'casechecker-delete-summary')
                                    newText = i18n.twtranslate(
                                        self.site,
                                        'casechecker-delete-reason',
                                        redirTitle)
                                    if newText:
                                        src.text = '{{delete}}\n\n' + newText
                                        src.save(editSummary, minor=False)
                                        changed = True

                            elif not dst.exists():
                                src = self.Page(title)
                                if page['ns'] == 14:
                                    dst = self.Page(newTitle)
                                    bot = CategoryMoveBot(
                                        src.title(with_ns=False),
                                        dst.title(with_ns=False),
                                        self.autonomous,
                                        editSummary + ' '
                                        + self.MakeMoveSummary(title,
                                                               newTitle),
                                        True)
                                    bot.run()
                                else:
                                    src.move(newTitle, editSummary,
                                             movesubpages=True)
                                changed = True

                    if not changed:
                        if err[1]:
                            self.AppendLineToLog(self.failedTitles, title)
                        else:
                            self.AddNoSuggestionTitle(title)

                        self.WikiLog('* ' + err[0])
                        printed = True

            if self.links:
                allLinks = []
                if 'links' in page:
                    allLinks += page['links']
                if 'categories' in page:
                    allLinks += page['categories']

                if allLinks:
                    pageObj = None
                    pageTxt = None
                    msg = []
                    foundSuggestions = False

                    for link in allLinks:
                        ltxt = link['title']
                        err = self.ProcessTitle(ltxt)
                        if err:
                            if err[1]:
                                foundSuggestions = True
                            elif self.AddNoSuggestionTitle(ltxt):
                                continue

                            newTitle = None
                            if self.replace:
                                newTitle = self.PickTarget(title, ltxt, err[1])
                                if newTitle:
                                    if pageObj is None:
                                        pageObj = self.Page(title)
                                        pageTxt = pageObj.get()

                                    msg.append(self.MakeMoveSummary(ltxt,
                                                                    newTitle))

                                    pageTxt = self.ReplaceLink(pageTxt, ltxt,
                                                               newTitle)
                            if not newTitle:
                                if not printed:
                                    self.WikiLog('* {}: link to {}'
                                                 .format(self.MakeLink(title,
                                                                       False),
                                                         err[0]))
                                    printed = True
                                else:
                                    self.WikiLog('** link to {}'
                                                 .format(err[0]))
                    if pageObj is not None:
                        if self.PutNewPage(pageObj, pageTxt, msg):
                            # done, no need to log anything
                            foundSuggestions = False

                    if foundSuggestions:
                        self.AppendLineToLog(self.failedTitles, title)

            if self.stopAfter:
                self.stopAfter -= 1
                if self.stopAfter == 0:
                    raise ValueError('Stopping because we are done')

    def WikiLog(self, text):
        """Write log."""
        pywikibot.output(text)
        self.wikilog.write(text + '\n')
        self.wikilog.flush()

    def FindBadWords(self, title):
        """Retrieve bad words."""
        for m in self.badWordPtrn.finditer(title):
            yield title[m.span()[0]:m.span()[1]]

    def ProcessTitle(self, title):
        """Process title."""
        badWords = list(self.FindBadWords(title))
        if badWords:
            # Allow known words, allow any roman numerals with local suffixes
            badWords = {i for i in badWords
                        if i not in self.knownWords
                        and self.romanNumSfxPtrn.match(i) is not None}

        if not badWords or self.Page(title).is_filepage():
            return None

        count = 0
        ambigBadWords = set()
        ambigBadWordsCount = 0
        mapLcl = {}
        mapLat = {}

        for badWord in badWords:
            # See if it would make sense to treat the whole word as either
            # cyrilic or latin
            mightBeLat = mightBeLcl = True
            for letter in badWord:
                if letter in self.localLtr:
                    if mightBeLat and letter not in self.localSuspects:
                        mightBeLat = False
                else:
                    if mightBeLcl and letter not in self.latinSuspects:
                        mightBeLcl = False
                    if letter not in ascii_letters:
                        raise ValueError('Assert failed')

            # Some words are well known and frequently mixed-typed
            if mightBeLcl and mightBeLat:
                if badWord in self.alwaysInLocal:
                    mightBeLat = False
                elif badWord in self.alwaysInLatin:
                    mightBeLcl = False

            if mightBeLcl:
                mapLcl[badWord] = badWord.translate(self.latToLclDict)
            if mightBeLat:
                mapLat[badWord] = badWord.translate(self.lclToLatDict)
            if mightBeLcl and mightBeLat:
                ambigBadWords.add(badWord)
                # Cannot do len(ambigBadWords) because they might be duplicates
                ambigBadWordsCount += 1

            if not mightBeLcl and not mightBeLat:
                # try to match one of the knownWords
                bwLen = len(badWord)
                kw = [w for w in self.knownWords if len(w) == bwLen]
                for p in range(bwLen):
                    if not kw:
                        break
                    c = badWord[p]
                    co = ord(c)
                    if co in self.latToLclDict:
                        c2 = self.latToLclDict[co]
                    elif co in self.lclToLatDict:
                        c2 = self.lclToLatDict[co]
                    else:
                        c2 = None
                    kw = [w for w in kw if p < len(w)
                          and (w[p] == c or (c2 is not None and w[p] == c2))]
                if len(kw) > 1:
                    pywikibot.output("Word '{}' could be treated as more than "
                                     'one known words'.format(badWord))
                elif len(kw) == 1:
                    mapLcl[badWord] = kw[0]
            count += 1

        infoText = self.MakeLink(title)
        possibleAlternatives = []

        if len(mapLcl) + len(mapLat) - ambigBadWordsCount < count:
            # We cannot auto-translate - offer a list of suggested words
            suggestions = list(mapLcl.values()) + list(mapLat.values())
            if suggestions:
                infoText += ', word suggestions: ' + ', '.join(
                    self.ColorCodeWord(t) for t in suggestions)
            else:
                infoText += ', no suggestions'
        else:
            # Replace all unambiguous bad words
            for k, v in dict(chain(mapLat.items(), mapLcl.items())).items():
                if k not in ambigBadWords:
                    title = title.replace(k, v)
            if not ambigBadWords:
                # There are no ambiguity, we can safelly convert
                possibleAlternatives.append(title)
                infoText += ', convert to ' + self.MakeLink(title)
            else:
                # Try to pick 0, 1, 2, ..., len(ambiguous words) unique
                # combinations from the bad words list, and convert just the
                # picked words to cyrilic, whereas making all other words as
                # latin character.
                for itemCntToPick in range(len(ambigBadWords) + 1):
                    title2 = title
                    for uc in combinations(list(ambigBadWords), itemCntToPick):
                        wordsToLat = ambigBadWords.copy()
                        for bw in uc:
                            title2 = title2.replace(bw, mapLcl[bw])
                            wordsToLat.remove(bw)
                        for bw in wordsToLat:
                            title2 = title2.replace(bw, mapLat[bw])
                        possibleAlternatives.append(title2)

                if possibleAlternatives:
                    infoText += ', can be converted to ' + ', '.join(
                        self.MakeLink(t) for t in possibleAlternatives)
                else:
                    infoText += ', no suggestions'
        return (infoText, possibleAlternatives)

    def PickTarget(self, title, original, candidates):
        """Pick target from candidates."""
        if not candidates:
            return None

        if len(candidates) == 1:
            return candidates[0]

        pagesDontExist = []
        pagesRedir = {}
        pagesExist = []

        for newTitle in candidates:
            dst = self.Page(newTitle)
            if not dst.exists():
                pagesDontExist.append(newTitle)
            elif dst.isRedirectPage():
                pagesRedir[newTitle] = dst.getRedirectTarget().title()
            else:
                pagesExist.append(newTitle)

        if len(pagesExist) == 1:
            return pagesExist[0]

        if not pagesExist and pagesRedir:
            if len(pagesRedir) == 1:
                return list(pagesRedir.keys())[0]

            t = None
            for v in pagesRedir.values():
                if not t:
                    t = v  # first item
                elif t != v:
                    break
            else:
                # all redirects point to the same target
                # pick the first one, doesn't matter what it is
                return list(pagesRedir.keys())[0]

        if not self.autonomous:
            pywikibot.output('Could not auto-decide for page {}. Which link '
                             'should be chosen?'
                             .format(self.MakeLink(title, False)))
            pywikibot.output('Original title: ', newline=False)
            self.ColorCodeWord(original + '\n', True)
            for count, t in enumerate(candidates, 1):
                if t in pagesDontExist:
                    msg = 'missing'
                elif t in pagesRedir:
                    msg = 'Redirect to ' + pagesRedir[t]
                else:
                    msg = 'page exists'
                self.ColorCodeWord('  {}: {} ({})\n'.format(count, t, msg),
                                   True)
            answers = [('skip', 's')] + [(str(i), i) for i in range(1, count)]
            choice = pywikibot.input_choice('Which link to choose?', answers)
            if choice != 's':
                return candidates[int(choice) - 1]

    def ColorCodeWord(self, word, toScreen=False):
        """Colorize code word."""
        if not toScreen:
            return self._ColorCodeWordHtml(word)
        return self._ColorCodeWordScreen(word)

    def _ColorCodeWordHtml(self, word):
        res = '<b>'
        lastIsCyr = word[0] in self.localLtr
        if lastIsCyr:
            res += self.lclClrFnt
        else:
            res += self.latClrFnt

        for letter in word:
            if letter in self.localLtr:
                if not lastIsCyr:
                    res += self.suffixClr + self.lclClrFnt
                    lastIsCyr = True
            elif letter in ascii_letters:
                if lastIsCyr:
                    res += self.suffixClr + self.latClrFnt
                    lastIsCyr = False
            res += letter

        return res + self.suffixClr + '</b>'

    def _ColorCodeWordScreen(self, word):
        res = ''
        lastIsCyr = word[0] in self.localLtr
        if lastIsCyr:
            res += self.colorFormatLocalColor
        else:
            res += self.colorFormatLatinColor

        for letter in word:
            if letter in self.localLtr:
                if not lastIsCyr:
                    res += self.colorFormatLocalColor
                    lastIsCyr = True
            elif letter in self.latLtr:
                if lastIsCyr:
                    res += self.colorFormatLatinColor
                    lastIsCyr = False
            res += letter

        return formatter.color_format(res + self.colorFormatSuffix)

    def AddNoSuggestionTitle(self, title):
        """Add backlinks to log."""
        if title in self.seenUnresolvedLinks:
            return True

        self.seenUnresolvedLinks.add(title)
        params = {
            'action': 'query',
            'list': 'backlinks',
            'bltitle': title,
            'bllimit': '50',
        }

        req = api.Request(site=self.site, parameters=params)
        data = req.submit()
        cl = 0
        redirs = 0
        if 'backlinks' in data['query']:
            bl = data['query']['backlinks']
            cl = len(bl)
            redirs = len([i for i in bl if 'redirect' in i])

        if cl and 'query-continue' in data:
            count = '50+'
        else:
            count = str(cl or 'no backlinks')

        self.AppendLineToLog(self.nosuggestions, '* {} ({}{})'
                             .format(self.MakeLink(title), count,
                                     ', {} redirects'
                                     .format(redirs if redirs > 0 else '')))
        return False

    def PutNewPage(self, pageObj, pageTxt, msg):
        """Save new page."""
        title = pageObj.title(as_link=True, textlink=True)
        coloredMsg = ', '.join(self.ColorCodeWord(m) for m in msg)
        if pageObj.text == pageTxt:
            self.WikiLog('* Error: Text replacement failed in {} ({})'
                         .format(self.MakeLink(title, False), coloredMsg))
        else:
            pywikibot.output('Case Replacements: {}'.format(', '.join(msg)))
            pageObj.text = pageTxt
            try:
                pageObj.save(
                    '{}: {}'.format(
                        i18n.twtranslate(
                            self.site, 'casechecker-replacement-summary'),
                        self.site.mediawiki_message(
                            'comma-separator').join(msg)))
                return True
            except (LockedPageError, PageSaveRelatedError):
                self.WikiLog('* Error: Could not save updated page {} ({})'
                             .format(self.MakeLink(title, False), coloredMsg))
        return False

    def MakeMoveSummary(self, fromTitle, toTitle):
        """Move summary from i18n."""
        return i18n.twtranslate(self.site, 'casechecker-replacement-linklist',
                                {'source': fromTitle, 'target': toTitle})

    def MakeLink(self, title, colorcode=True):
        """Create a colored link string."""
        prf = '' if self.Page(title).namespace() == 0 else ':'
        cc = '|««« {} »»»'.format(
            self.ColorCodeWord(title) if colorcode else '')
        return '[[{}{}{}]]'.format(prf, title, cc)

    def OpenLogFile(self, filename):
        """Open logfile."""
        try:
            return codecs.open(filename, 'a', 'utf-8')
        except IOError:
            return codecs.open(filename, 'w', 'utf-8')

    def AppendLineToLog(self, filename, text):
        """Write text to logfile."""
        with self.OpenLogFile(filename) as f:
            f.write(text + '\n')

    def Page(self, title):
        """Create Page object from title."""
        return pywikibot.Page(self.site, title)

    def ReplaceLink(self, text, oldtxt, newtxt):
        """Replace links."""
        frmParts = [s.strip(self.stripChars)
                    for s in self.wordBreaker.split(oldtxt)]
        toParts = [s.strip(self.stripChars)
                   for s in self.wordBreaker.split(newtxt)]

        if len(frmParts) != len(toParts):
            raise ValueError('Splitting parts do not match counts')

        for i, part in enumerate(frmParts):
            if part != len(toParts[i]):
                raise ValueError('Splitting parts do not match word length')
            if part:
                text = text.replace(first_lower(part), first_lower(toParts[i]))
                text = text.replace(first_upper(part), first_upper(toParts[i]))
        return text


if __name__ == '__main__':
    bot = CaseChecker()
    bot.Run()
