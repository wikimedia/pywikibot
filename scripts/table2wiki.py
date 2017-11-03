#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Nifty script to convert HTML-tables to MediaWiki's own syntax.

These command line parameters can be used to specify which pages to work on:

&params;

-always           The bot won't ask for confirmation when putting a page

-skipwarning      Skip processing a page when a warning occurred.
                  Only used when -always is or becomes True.

-quiet            Don't show diffs in -always mode

-mysqlquery       Retrieve information from a local mirror.
                  Searches for pages with HTML tables, and tries to convert
                  them on the live wiki.

-xml              Retrieve information from a local XML dump
                  (pages_current, see https://download.wikimedia.org).
                  Argument can also be given as "-xml:filename".
                  Searches for pages with HTML tables, and tries to convert
                  them on the live wiki.

Example:

      pwb.py table2wiki -xml:20050713_pages_current.xml -lang:de

FEATURES
Save against missing </td>
Corrects attributes of tags

KNOWN BUGS
Broken HTML tables will most likely result in broken wiki tables!
Please check every article you change.
"""
#
# (C) 2003 Thomas R. Koll, <tomk32@tomk32.de>
# (C) Pywikibot team, 2003-2017
#
# Distributed under the terms of the MIT license.
#
# Automatically ported from compat branch by compat2core.py script
#
from __future__ import absolute_import, unicode_literals

import re

import pywikibot
from pywikibot import config
from pywikibot import i18n
from pywikibot import pagegenerators
from pywikibot import xmlreader

from pywikibot.bot import (SingleSiteBot, ExistingPageBot, NoRedirectPageBot,
                           suggest_help, input_yn)
from pywikibot.exceptions import ArgumentDeprecationWarning
from pywikibot.tools import has_module, issue_deprecation_warning

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;': pagegenerators.parameterHelp,
}


class TableXmlDumpPageGenerator(object):
    """Generator to yield all pages that seem to contain an HTML table."""

    def __init__(self, xmlfilename):
        """Constructor."""
        self.xmldump = xmlreader.XmlDump(xmlfilename)

    def __iter__(self):
        tableTagR = re.compile('<table', re.IGNORECASE)
        for entry in self.xmldump.parse():
            if tableTagR.search(entry.text):
                yield pywikibot.Page(pywikibot.Site(), entry.title)


class Table2WikiRobot(SingleSiteBot, ExistingPageBot, NoRedirectPageBot):

    """Bot to convert HTML tables to wiki syntax.

    @param generator: the page generator that determines on which pages
        to work
    @type generator: generator
    """

    def __init__(self, **kwargs):
        """Constructor."""
        self.availableOptions.update({
            'quiet': False,       # quiet mode, less output
            'skipwarning': False  # on warning skip that page
        })

        super(Table2WikiRobot, self).__init__(site=True, **kwargs)

    def convertTable(self, table):
        """
        Convert an HTML table to wiki syntax.

        If the table already is a
        wiki table or contains a nested wiki table, tries to beautify it.
        Returns the converted table, the number of warnings that occured and
        a list containing these warnings.
        Hint: if you give an entire page text as a parameter instead of a table
        only, this function will convert all HTML tables and will also try to
        beautify all wiki tables already contained in the text.
        """
        warnings = 0
        # this array will contain strings that will be shown in case of
        # possible errors, before the user is asked if he wants to accept the
        # changes.
        warning_messages = []
        newTable = table
        ##################
        # bring every <tag> into one single line.
        num = 1
        while num != 0:
            newTable, num = re.subn(r'([^\r\n]{1})(<[tT]{1}[dDhHrR]{1})',
                                    r'\1\r\n\2', newTable)

        ##################
        # every open-tag gets a new line.

        ##################
        # Note that we added the ## characters in markActiveTables().
        # <table> tag with attributes, with more text on the same line
        newTable = re.sub(
            r'(?i)[\r\n]*?<##table## (?P<attr>[\w\W]*?)>'
            r'(?P<more>[\w\W]*?)[\r\n ]*',
            r'\r\n{| \g<attr>\r\n\g<more>', newTable)
        # <table> tag without attributes, with more text on the same line
        newTable = re.sub(r'(?i)[\r\n]*?<##table##>(?P<more>[\w\W]*?)[\r\n ]*',
                          r'\r\n{|\n\g<more>\r\n', newTable)
        # <table> tag with attributes, without more text on the same line
        newTable = re.sub(
            r'(?i)[\r\n]*?<##table## (?P<attr>[\w\W]*?)>[\r\n ]*',
            r'\r\n{| \g<attr>\r\n', newTable)
        # <table> tag without attributes, without more text on the same line
        newTable = re.sub(r'(?i)[\r\n]*?<##table##>[\r\n ]*',
                          '\r\n{|\r\n', newTable)
        # end </table>
        newTable = re.sub(r'(?i)[\s]*<\/##table##>',
                          '\r\n|}', newTable)

        ##################
        # caption with attributes
        newTable = re.sub(
            r'(?i)<caption (?P<attr>[\w\W]*?)>'
            r'(?P<caption>[\w\W]*?)<\/caption>',
            r'\r\n|+\g<attr> | \g<caption>', newTable)
        # caption without attributes
        newTable = re.sub(r'(?i)<caption>(?P<caption>[\w\W]*?)<\/caption>',
                          r'\r\n|+ \g<caption>', newTable)

        ##################
        # <th> often people don't write them within <tr>, be warned!
        # <th> with attributes
        newTable = re.sub(
            r"(?i)[\r\n]+<th(?P<attr> [^>]*?)>(?P<header>[\w\W]*?)<\/th>",
            r"\r\n!\g<attr> | \g<header>\r\n", newTable)

        # <th> without attributes
        newTable = re.sub(r"(?i)[\r\n]+<th>(?P<header>[\w\W]*?)<\/th>",
                          r'\r\n! \g<header>\r\n', newTable)

        # fail save. sometimes people forget </th>
        # <th> without attributes, without closing </th>
        newTable, n = re.subn(r'(?i)[\r\n]+<th>(?P<header>[\w\W]*?)[\r\n]+',
                              r'\r\n! \g<header>\r\n', newTable)
        if n > 0:
            warning_messages.append(
                u'WARNING: found <th> without </th>. (%d occurences)\n' % n)
            warnings += n

        # <th> with attributes, without closing </th>
        newTable, n = re.subn(
            r'(?i)[\r\n]+<th(?P<attr> [^>]*?)>(?P<header>[\w\W]*?)[\r\n]+',
            r'\n!\g<attr> | \g<header>\r\n', newTable)
        if n > 0:
            warning_messages.append(
                'WARNING: found <th ...> without </th>. (%d occurences\n)' % n)
            warnings += n

        ##################
        # <tr> with attributes
        newTable = re.sub("(?i)[\r\n]*<tr(?P<attr> [^>]*?)>[\r\n]*",
                          r"\r\n|-\g<attr>\r\n", newTable)

        # <tr> without attributes
        newTable = re.sub("(?i)[\r\n]*<tr>[\r\n]*",
                          r"\r\n|-\r\n", newTable)

        ##################
        # normal <td> without arguments
        newTable = re.sub(r'(?i)[\r\n]+<td>(?P<cell>[\w\W]*?)<\/td>',
                          r'\r\n| \g<cell>\r\n', newTable)

        ##################
        # normal <td> with arguments
        newTable = re.sub(
            r'(?i)[\r\n]+<td(?P<attr> [^>]*?)>(?P<cell>[\w\W]*?)<\/td>',
            r'\r\n|\g<attr> | \g<cell>', newTable)

        # WARNING: this sub might eat cells of bad HTML, but most likely it
        # will correct errors
        # TODO: some more docu please
        newTable, n = re.subn("(?i)[\r\n]+<td>(?P<cell>[^\r\n]*?)<td>",
                              r"\r\n| \g<cell>\r\n", newTable)
        if n > 0:
            warning_messages.append(
                u'<td> used where </td> was expected. (%d occurences)\n' % n)
            warnings += n

        # what is this for?
        newTable, n = re.subn(
            r'[\r\n]+<(td|TD)([^>]+?)>([^\r\n]*?)</(td|TD)>',
            r'\r\n|\2 | \3\r\n', newTable)
        if n > 0:
            warning_messages.append(
                u"WARNING: (sorry, bot code unreadable (1). I don't know why "
                u"this warning is given.) (%d occurences)\n" % n)

        # fail save. sometimes people forget </td>
        # <td> without arguments, with missing </td>
        newTable, n = re.subn(r'(?i)<td>(?P<cell>[^<]*?)[\r\n]+',
                              r'\r\n| \g<cell>\r\n', newTable)
        if n > 0:
            warning_messages.append(u"NOTE: Found <td> without </td>. This "
                                    u"shouldn't cause problems.\n")

        # <td> with attributes, with missing </td>
        newTable, n = re.subn(
            r'(?i)[\r\n]*<td(?P<attr> [^>]*?)>(?P<cell>[\w\W]*?)[\r\n]+',
            r'\r\n|\g<attr> | \g<cell>\r\n', newTable)
        if n > 0:
            warning_messages.append(u"NOTE: Found <td> without </td>. This "
                                    u"shouldn't cause problems.\n")

        ##################
        # Garbage collecting ;-)
        newTable = re.sub(r'(?i)<td>[\r\n]*<\/tr>', '', newTable)
        # delete closing tags
        newTable = re.sub(r'(?i)[\r\n]*<\/t[rdh]>', '', newTable)

        ##################
        # OK, that's only theory but works most times.
        # Most browsers assume that <th> gets a new row and we do the same
        #        newTable, n = re.subn("([\r\n]+\|\ [^\r\n]*?)([\r\n]+\!)",
        #                             "\\1\r\n|-----\\2", newTable)
        #        warnings = warnings + n
        # adds a |---- below for the case the new <tr> is missing
        #        newTable, n = re.subn("([\r\n]+\!\ [^\r\n]*?[\r\n]+)(\|\ )",
        #                             "\\1|-----\r\n\\2", newTable)
        #        warnings = warnings + n

        ##################
        # most <th> come with '''title'''. Senseless in my eyes cuz
        # <th> should be bold anyways.
        newTable = re.sub(r"[\r\n]+\!([^'\n\r]*)'''([^'\r\n]*)'''",
                          r'\r\n!\1\2', newTable)

        ##################
        # kills indention within tables. Be warned, it might seldom bring
        # bad results.
        # True by default. Set 'deIndentTables = False' in user-config.py
        if config.deIndentTables:
            num = 1
            while num != 0:
                newTable, num = re.subn(
                    r'(\{\|[\w\W]*?)\n[ \t]+([\w\W]*?\|\})',
                    r'\1\r\n\2', newTable)

        ##################
        # kills additional spaces after | or ! or {|
        # This line was creating problems, so I commented it out --Daniel
        # newTable = re.sub("[\r\n]+\|[\t ]+?[\r\n]+", "\r\n| ", newTable)
        # kills trailing spaces and tabs
        newTable = re.sub(r'\r\n(.*)[\t\ ]+[\r\n]+',
                          r'\r\n\1\r\n', newTable)
        # kill extra new-lines
        newTable = re.sub(r'[\r\n]{4,}(\!|\|)',
                          r'\r\n\1', newTable)

        ##################
        # shortening if <table> had no arguments/parameters
        newTable = re.sub(r'[\r\n]+\{\|[\ ]+\| ', r'\r\n{| ', newTable)
        # shortening if <td> had no articles
        newTable = re.sub(r'[\r\n]+\|[\ ]+\| ', '\r\n| ', newTable)
        # shortening if <th> had no articles
        newTable = re.sub(r'\n\|\+[\ ]+\|', '\n|+ ', newTable)
        # shortening of <caption> had no articles
        newTable = re.sub(r'[\r\n]+\![\ ]+\| ', '\r\n! ', newTable)

        ##################
        # proper attributes. attribute values need to be in quotation marks.
        num = 1
        while num != 0:
            # group 1 starts with newlines, followed by a table or row tag
            # ( {| or |--- ), then zero or more attribute key - value
            # pairs where the value already has correct quotation marks, and
            # finally the key of the attribute we want to fix here.
            # group 2 is the value of the attribute we want to fix here.
            # We recognize it by searching for a string of non-whitespace
            # characters
            # - [^\s]+? - which is not embraced by quotation marks - [^"]
            newTable, num = re.subn(
                r'([\r\n]+(?:\|-|\{\|)[^\r\n\|]+) *= *([^"\s>]+)',
                r'\1="\2"', newTable, 1)

        num = 1
        while num != 0:
            # The same for header and cell tags ( ! or | ), but for these tags
            # the attribute part is finished by a | character. We don't want to
            # change cell contents which accidentially contain an equal sign.
            # Group 1 and 2 are anologously to the previous regular expression,
            # group 3 are the remaining attribute key - value pairs.
            newTable, num = re.subn(
                r'([\r\n]+(?:!|\|)[^\r\n\|]+) *= *([^"\s>]+)([^\|\r\n]*)\|',
                r'\1="\2"\3|', newTable, 1)

        ##################
        # merge two short <td>s
        num = 1
        while num != 0:
            newTable, num = re.subn(
                r'[\r\n]+(\|[^\|\-\}]{1}[^\n\r]{0,35})'
                r'[\r\n]+(\|[^\|\-\}]{1}[^\r\n]{0,35})[\r\n]+',
                r'\r\n\1 |\2\r\n', newTable)
        ####
        # add a new line if first is * or #
        newTable = re.sub(r'[\r\n]+\| ([*#]{1})',
                          r'\r\n|\r\n\1', newTable)

        ##################
        # strip <center> from <th>
        newTable = re.sub(r'([\r\n]+\![^\r\n]+?)<center>([\w\W]+?)<\/center>',
                          r'\1 \2', newTable)
        # strip align="center" from <th> because the .css does it
        # if there are no other attributes than align, we don't need
        # that | either
        newTable = re.sub(r'([\r\n]+\! +)align\=\"center\" +\|',
                          r'\1', newTable)
        # if there are other attributes, simply strip the align="center"
        newTable = re.sub(
            r'([\r\n]+\![^\r\n\|]+?)align\=\"center\"([^\n\r\|]+?\|)',
            r'\1 \2', newTable)

        ##################
        # kill additional spaces within arguments
        num = 1
        while num != 0:
            newTable, num = re.subn(
                r'[\r\n]+(\||\!)([^|\r\n]*?)[ \t]{2,}([^\r\n]+?)',
                r'\r\n\1\2 \3', newTable)

        ##################
        # I hate those long lines because they make a wall of letters
        # Off by default, set 'splitLongParagraphs = True' in user-config.py
        if config.splitLongParagraphs:
            num = 1
            while num != 0:
                # TODO: how does this work? docu please.
                # why are only äöüß used, but not other special characters?
                newTable, num = re.subn(
                    r'(\r\n[A-Z]{1}[^\n\r]{200,}?[a-zäöüß]\.)'
                    r'\ ([A-ZÄÖÜ]{1}[^\n\r]{200,})',
                    r'\1\r\n\2', newTable)
        return newTable, warnings, warning_messages

    def markActiveTables(self, text):
        """
        Mark all hidden table start and end tags.

        Mark all table start and end tags that are not disabled by nowiki tags,
        comments etc. We will then later only work on these marked tags.
        """
        tableStartTagR = re.compile("<table", re.IGNORECASE)
        tableEndTagR = re.compile("</table>", re.IGNORECASE)

        text = pywikibot.replaceExcept(text, tableStartTagR, "<##table##",
                                       exceptions=['comment', 'math',
                                                   'nowiki', 'pre', 'source'])
        text = pywikibot.replaceExcept(text, tableEndTagR, "</##table##>",
                                       exceptions=['comment', 'math',
                                                   'nowiki', 'pre', 'source'])
        return text

    def findTable(self, text):
        """
        Find the first HTML table (which can contain nested tables).

        Returns the table and the start and end position inside the text.
        """
        # Note that we added the ## characters in markActiveTables().
        markedTableStartTagR = re.compile("<##table##", re.IGNORECASE)
        markedTableEndTagR = re.compile("</##table##>", re.IGNORECASE)
        m = markedTableStartTagR.search(text)
        if not m:
            return None, 0, 0
        else:
            start = m.start()
            offset = m.end()
            originalText = text
            text = text[m.end():]
            # depth level of table nesting
            depth = 1
            # i = start + 1
            while depth > 0:
                nextStarting = markedTableStartTagR.search(text)
                nextEnding = markedTableEndTagR.search(text)
                if not nextEnding:
                    pywikibot.output(
                        'More opening than closing table tags. Skipping.')
                    return None, 0, 0
                # if another table tag is opened before one is closed
                elif (nextStarting and
                      nextStarting.start() < nextEnding.start()):
                    offset += nextStarting.end()
                    text = text[nextStarting.end():]
                    depth += 1
                else:
                    offset += nextEnding.end()
                    text = text[nextEnding.end():]
                    depth -= 1
            end = offset
            return originalText[start:end], start, end

    def convertAllHTMLTables(self, text):
        """
        Convert all HTML tables in text to wiki syntax.

        Returns the converted text, the number of converted tables and the
        number of warnings that occured.
        """
        text = self.markActiveTables(text)

        convertedTables = 0
        warningSum = 0
        warningMessages = u''

        while True:
            table, start, end = self.findTable(text)
            if not table:
                # no more HTML tables left
                break

            # convert the current table
            newTable, warningsThisTable, warnMsgsThisTable = self.convertTable(
                table)
            warningSum += warningsThisTable
            for msg in warnMsgsThisTable:
                warningMessages += 'In table %i: %s' % (convertedTables + 1,
                                                        msg)
            text = text[:start] + newTable + text[end:]
            convertedTables += 1

        pywikibot.output(warningMessages)
        return text, convertedTables, warningSum

    def treat_page(self):
        """Convert all HTML tables in text to wiki syntax and save it."""
        text = self.current_page.text
        newText, convertedTables, warnings = self.convertAllHTMLTables(text)

        # Check if there are any marked tags left
        markedTableTagR = re.compile("<##table##|</##table##>", re.IGNORECASE)
        if markedTableTagR.search(newText):
            pywikibot.error(
                u'not all marked table start or end tags processed!')
            return

        if convertedTables == 0:
            pywikibot.output(u"No changes were necessary.")
            return

        if warnings:
            if self.getOption('always') and self.getOption('skipwarning'):
                pywikibot.output(
                    'There were %i replacements that might lead to bad '
                    'output. Skipping.' % warnings)
                return
            if not self.getOption('always'):
                pywikibot.output(
                    'There were %i replacements that might lead to bad '
                    'output.' % warnings)
                if not input_yn('Do you want to change the page anyway'):
                    return

        # get edit summary message
        if warnings == 0:
            editSummaryMessage = i18n.twtranslate(
                self.site.code, 'table2wiki-no-warning')
        else:
            editSummaryMessage = i18n.twntranslate(
                self.site.code,
                'table2wiki-warnings',
                {'count': warnings}
            )
        self.put_current(newText, summary=editSummaryMessage,
                         show_diff=not (self.getOption('quiet') and
                                        self.getOption('always')))


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    options = {}
    gen = None

    local_args = pywikibot.handle_args(args)

    # This factory is responsible for processing command line arguments
    # that are also used by other scripts and that determine on which pages
    # to work on.
    genFactory = pagegenerators.GeneratorFactory(positional_arg_name='page')

    for arg in local_args:
        option, sep, value = arg.partition(':')
        if option == '-xml':
            filename = value or pywikibot.input(
                "Please enter the XML dump's filename:")
            gen = TableXmlDumpPageGenerator(filename)
        elif option == '-auto':
            issue_deprecation_warning(
                'The usage of "-auto"', '-always',
                1, ArgumentDeprecationWarning)
            options['always'] = True
        elif option in ['-always', '-quiet', '-skipwarning']:
            options[option[1:]] = True
        else:
            if option in ['-sql', '-mysqlquery']:
                if not (has_module('oursql') or has_module('MySQLdb')):
                    raise NotImplementedError(
                        'Neither "oursql" nor "MySQLdb" library is installed.')
                if option == '-sql':
                    issue_deprecation_warning(
                        'The usage of "-sql"', '-mysqlquery',
                        1, ArgumentDeprecationWarning)

                query = value or """
SELECT page_namespace, page_title
FROM page JOIN text ON (page_id = old_id)
WHERE old_text LIKE '%<table%'
"""
                arg = '-mysqlquery:' + query
            genFactory.handleArg(arg)

    if gen:
        gen = pagegenerators.NamespaceFilterPageGenerator(
            gen, genFactory.namespaces)
    else:
        gen = genFactory.getCombinedGenerator()

    if gen:
        if not genFactory.nopreload:
            gen = pagegenerators.PreloadingGenerator(gen)
        bot = Table2WikiRobot(generator=gen, **options)
        bot.run()
        return True
    else:
        suggest_help(missing_generator=True)
        return False


if __name__ == "__main__":
    main()
