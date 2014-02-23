#!/usr/bin/python
#coding: utf-8
"""
This bot takes its input from a file that contains a number of
pages to be put on the wiki. The pages should all have the same
begin and end text (which may not overlap).

By default the text should have the intended title of the page
as the first text in bold (that is, between ''' and '''),
you can modify this behavior with command line options.

The default is not to include the begin and
end text in the page, if you want to include that text, use
the -include option.

Specific arguments:
-start:xxx      Specify the text that marks the beginning of a page
-end:xxx        Specify the text that marks the end of a page
-file:xxx       Give the filename we are getting our material from
-include        The beginning and end markers should be included
                in the page.
-titlestart:xxx Use xxx in place of ''' for identifying the
                beginning of page title
-titleend:xxx   Use xxx in place of ''' for identifying the
                end of page title
-notitle        do not include the title, including titlestart, and
                titleend, in the page
-nocontent      If page has this statment it dosen't append
                (example: -nocontent:"{{infobox")
-summary:xxx    Use xxx as the edit summary for the upload - if
                a page exists, standard messages are appended
                after xxx for appending, prepending, or replacement
-autosummary    Use MediaWikis autosummary when creating a new page,
                overrides -summary in this case
-minor          set minor edit flag on page edits

If the page to be uploaded already exists:
-safe           do nothing (default)
-appendtop      add the text to the top of it
-appendbottom   add the text to the bottom of it
-force          overwrite the existing page
"""
#
# (C) Andre Engels, 2004
# (C) Pywikipedia bot team, 2005-2010
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import re
import codecs
import pywikibot
from pywikibot import config


class NoTitle(Exception):
    """No title found"""
    def __init__(self, offset):
        self.offset = offset


class PageFromFileRobot:
    """
    Responsible for writing pages to the wiki, with the titles and contents
    given by a PageFromFileReader.
    """

    msg = {
        'ar': u'استيراد تلقائي للمقالات',
        'de': u'Automatischer Import von Artikeln',
        'en': u'Automated import of articles',
        'fa': u'درون‌ریزی خودکار مقاله‌ها',
        'fr': u'Import automatique',
        'he': u'ייבוא ערכים אוטומטי',
        'ia': u'Importation automatic de articulos',
        'id': u'Impor artikel automatis',
        'it': u'Caricamento automatico',
        'ja': u'記事の自動取り込み',
        'ksh': u'Bot: automatesch huhjelaade',
        'mzn': u'ربوت:صفحه شه خاد به خاد دله دکته',
        'nl': u'Geautomatiseerde import',
        'no': u'bot: Automatisk import',
        'pl': u'Automatyczny import artykułów',
        'pt': u'Importação automática de artigos',
        'uk': u'Автоматичний імпорт статей',
        'zh': u'機器人: 自動匯入頁面',
    }

    # The following messages are added to topic when the page already exists
    msg_top = {
        'ar': u'كتابة على الأعلى',
        'de': u'ergänze am Anfang',
        'en': u'append on top',
        'fa': u'به بالا اضافه شد',
        'he': u'הוספה בראש הדף',
        'fr': u'rajouté en haut',
        'id': u'ditambahkan di atas',
        'it': u'aggiungo in cima',
        'ja': u'冒頭への追加',
        'ksh': u'un dofüürjesaz',
        'nl': u'bovenaan toegevoegd',
        'no': u'legger til øverst',
        'pl': u'dodaj na górze',
        'pt': u'adicionado no topo',
        'uk': u'додано зверху',
        'zh': u'機器人: 增加至最上層',
    }

    msg_bottom = {
        'ar': u'كتابة على الأسفل',
        'de': u'ergänze am Ende',
        'en': u'append on bottom',
        'fa': u'به پایین اضافه شد',
        'he': u'הוספה בתחתית הדף',
        'fr': u'rajouté en bas',
        'id': u'ditambahkan di bawah',
        'it': u'aggiungo in fondo',
        'ja': u'末尾への追加',
        'ksh': u'un aanjehange',
        'nl': u'onderaan toegevoegd',
        'no': u'legger til nederst',
        'pl': u'dodaj na dole',
        'pt': u'adicionando no fim',
        'uk': u'додано знизу',
        'zh': u'機器人: 增加至最底層',
    }

    msg_force = {
        'ar': u'تمت الكتابة على النص الموجود',
        'de': u'bestehender Text überschrieben',
        'en': u'existing text overwritten',
        'fa': u'متن جایگزین شد',
        'he': u'הטקסט הישן נמחק',
        'fr': u'texte existant écrasé',
        'id': u'menimpa teks yang ada',
        'it': u'sovrascritto il testo esistente',
        'ja': u'存在するテキストの上書き',
        'ksh': u'un komplët ußjetuusch',
        'nl': u'bestaande tekst overschreven',
        'no': u'erstatter eksisterende tekst',
        'pl': u'aktualny tekst nadpisany',
        'pt': u'sobrescrever texto',
        'uk': u'існуючий текст перезаписано',
        'zh': u'機器人: 覆寫已存在的文字',
    }

    def __init__(self, reader, force, append, summary, minor, autosummary,
                 nocontent):
        self.reader = reader
        self.force = force
        self.append = append
        self.summary = summary
        self.minor = minor
        self.autosummary = autosummary
        self.nocontent = nocontent

    def run(self):
        for title, contents in self.reader.run():
            self.put(title, contents)

    def put(self, title, contents):
        mysite = pywikibot.getSite()

        page = pywikibot.Page(mysite, title)
        # Show the title of the page we're working on.
        # Highlight the title in purple.
        pywikibot.output(u">>> \03{lightpurple}%s\03{default} <<<"
                         % page.title())

        if self.summary:
            comment = self.summary
        else:
            comment = pywikibot.translate(mysite, self.msg)

        comment_top = comment + " - " + pywikibot.translate(mysite,
                                                            self.msg_top)
        comment_bottom = comment + " - " + pywikibot.translate(mysite,
                                                               self.msg_bottom)
        comment_force = comment + " *** " + pywikibot.translate(mysite,
                                                                self.msg_force) + " ***"

        # Remove trailing newlines (cause troubles when creating redirects)
        contents = re.sub('^[\r\n]*', '', contents)

        if page.exists():
            if self.nocontent != u'':
                pagecontents = page.get()
                if pagecontents.find(self.nocontent) != -1 or pagecontents.find(self.nocontent.lower()) != -1:
                    pywikibot.output(u'Page has %s so it is skipped' % (self.nocontent))
                    return
            if self.append == "Top":
                pywikibot.output(u"Page %s already exists, appending on top!"
                                     % title)
                contents = contents + page.get()
                comment = comment_top
            elif self.append == "Bottom":
                pywikibot.output(u"Page %s already exists, appending on bottom!"
                                     % title)
                contents = page.get() + contents
                comment = comment_bottom
            elif self.force:
                pywikibot.output(u"Page %s already exists, ***overwriting!"
                                 % title)
                comment = comment_force
            else:
                pywikibot.output(u"Page %s already exists, not adding!" % title)
                return
        else:
            if self.autosummary:
                comment = ''
                pywikibot.setAction('')
        try:
            page.put(contents, comment=comment, minorEdit=self.minor)
        except pywikibot.LockedPage:
            pywikibot.output(u"Page %s is locked; skipping." % title)
        except pywikibot.EditConflict:
            pywikibot.output(u'Skipping %s because of edit conflict' % title)
        except pywikibot.SpamfilterError as error:
            pywikibot.output(
                u'Cannot change %s because of spam blacklist entry %s'
                % (title, error.url))


class PageFromFileReader:
    """
    Responsible for reading the file.

    The run() method yields a (title, contents) tuple for each found page.
    """
    def __init__(self, filename, pageStartMarker, pageEndMarker,
                 titleStartMarker, titleEndMarker, include, notitle):
        self.filename = filename
        self.pageStartMarker = pageStartMarker
        self.pageEndMarker = pageEndMarker
        self.titleStartMarker = titleStartMarker
        self.titleEndMarker = titleEndMarker
        self.include = include
        self.notitle = notitle

    def run(self):
        pywikibot.output('Reading \'%s\'...' % self.filename)
        try:
            f = codecs.open(self.filename, 'r',
                            encoding=config.textfile_encoding)
        except IOError as err:
            pywikibot.output(str(err))
            return

        text = f.read()
        position = 0
        length = 0
        while True:
            try:
                length, title, contents = self.findpage(text[position:])
            except AttributeError:
                if not length:
                    pywikibot.output(u'\nStart or end marker not found.')
                else:
                    pywikibot.output(u'End of file.')
                break
            except NoTitle as err:
                pywikibot.output(u'\nNo title found - skipping a page.')
                position += err.offset
                continue

            position += length
            yield title, contents

    def findpage(self, text):
        pageR = re.compile(re.escape(self.pageStartMarker) + "(.*?)" +
                           re.escape(self.pageEndMarker), re.DOTALL)
        titleR = re.compile(re.escape(self.titleStartMarker) + "(.*?)" +
                            re.escape(self.titleEndMarker))

        location = pageR.search(text)
        if self.include:
            contents = location.group()
        else:
            contents = location.group(1)
        try:
            title = titleR.search(contents).group(1)
            if self.notitle:
                #Remove title (to allow creation of redirects)
                contents = titleR.sub('', contents, count=1)
        except AttributeError:
            raise NoTitle(location.end())
        else:
            return location.end(), title, contents


def main():
    # Adapt these to the file you are using. 'pageStartMarker' and
    # 'pageEndMarker' are the beginning and end of each entry. Take text that
    # should be included and does not occur elsewhere in the text.

    # TODO: make config variables for these.
    filename = "dict.txt"
    pageStartMarker = "{{-start-}}"
    pageEndMarker = "{{-stop-}}"
    titleStartMarker = u"'''"
    titleEndMarker = u"'''"
    nocontent = u""
    include = False
    force = False
    append = None
    notitle = False
    summary = None
    minor = False
    autosummary = False

    for arg in pywikibot.handleArgs():
        if arg.startswith("-start:"):
            pageStartMarker = arg[7:]
        elif arg.startswith("-end:"):
            pageEndMarker = arg[5:]
        elif arg.startswith("-file:"):
            filename = arg[6:]
        elif arg == "-include":
            include = True
        elif arg == "-appendtop":
            append = "Top"
        elif arg == "-appendbottom":
            append = "Bottom"
        elif arg == "-force":
            force = True
        elif arg == "-safe":
            force = False
            append = None
        elif arg == '-notitle':
            notitle = True
        elif arg == '-minor':
            minor = True
        elif arg.startswith('-nocontent:'):
            nocontent = arg[11:]
        elif arg.startswith("-titlestart:"):
            titleStartMarker = arg[12:]
        elif arg.startswith("-titleend:"):
            titleEndMarker = arg[10:]
        elif arg.startswith("-summary:"):
            summary = arg[9:]
        elif arg == '-autosummary':
            autosummary = True
        else:
            pywikibot.output(u"Disregarding unknown argument %s." % arg)

    reader = PageFromFileReader(filename, pageStartMarker, pageEndMarker,
                                titleStartMarker, titleEndMarker, include,
                                notitle)
    bot = PageFromFileRobot(reader, force, append, summary, minor, autosummary,
                            nocontent)
    bot.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
