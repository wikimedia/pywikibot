#!/usr/bin/python
"""
Nifty script to convert HTML-tables to MediaWiki's own syntax.

These command line parameters can be used to specify which pages to work on:

&params;

The following parameters are supported:

-always           The bot won't ask for confirmation when putting
                  a page.

-skipwarning      Skip processing a page when a warning occurred.
                  Only used when -always is or becomes True.

-quiet            Don't show diffs in -always mode.

-mysqlquery       Retrieve information from a local database mirror.
                  If no query specified, bot searches for pages with
                  HTML tables, and tries to convert them on the live
                  wiki.

-xml              Retrieve information from a local XML dump
                  (pages_current, see https://dumps.wikimedia.org).
                  Argument can also be given as "-xml:filename".
                  Searches for pages with HTML tables, and tries
                  to convert them on the live wiki.

Example:

    python pwb.py table2wiki -xml:20050713_pages_current.xml -lang:de

FEATURES

Save against missing </td>
Corrects attributes of tags

KNOWN BUGS

Broken HTML tables will most likely result in broken wiki tables!
Please check every article you change.
"""
#
# (C) Pywikibot team, 2003-2020
#
# Distributed under the terms of the MIT license.
#
# Automatically ported from compat branch by compat2core.py script
#
import re

import pywikibot
from pywikibot import config, i18n, pagegenerators, xmlreader
from pywikibot.bot import (
    ExistingPageBot,
    NoRedirectPageBot,
    SingleSiteBot,
    input_yn,
    suggest_help,
)
from pywikibot.textlib import replaceExcept


# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816


class TableXmlDumpPageGenerator:
    """Generator to yield all pages that seem to contain an HTML table."""

    def __init__(self, xmlfilename):
        """Initializer."""
        self.xmldump = xmlreader.XmlDump(xmlfilename)

    def __iter__(self):
        for entry in self.xmldump.parse():
            if _table_start_regex.search(entry.text):
                yield pywikibot.Page(pywikibot.Site(), entry.title)


class Table2WikiRobot(SingleSiteBot, ExistingPageBot, NoRedirectPageBot):

    """Bot to convert HTML tables to wiki syntax.

    :param generator: the page generator that determines on which pages
        to work
    :type generator: generator
    """

    def __init__(self, **kwargs):
        """Initializer."""
        self.available_options.update({
            'quiet': False,       # quiet mode, less output
            'skipwarning': False  # on warning skip that page
        })

        super().__init__(**kwargs)

    def convertTable(self, table):
        """
        Convert an HTML table to wiki syntax.

        If the table already is a
        wiki table or contains a nested wiki table, tries to beautify it.
        Returns the converted table, the number of warnings that occurred and
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
        new_table = table
        ##################
        # bring every <tag> into one single line.
        num = 1
        while num != 0:
            new_table, num = re.subn(
                r'([^\r\n]{1})(<[tT]{1}[dDhHrR]{1})', r'\1\r\n\2', new_table)

        ##################
        # every open-tag gets a new line.

        ##################
        # Note that we added the ## characters in markActiveTables().
        # <table> tag with attributes, with more text on the same line
        new_table = re.sub(
            r'(?i)[\r\n]*?<##table## (?P<attr>[\w\W]*?)>'
            r'(?P<more>[\w\W]*?)[\r\n ]*',
            r'\r\n{| \g<attr>\r\n\g<more>', new_table)
        # <table> tag without attributes, with more text on the same line
        new_table = re.sub(
            r'(?i)[\r\n]*?<##table##>(?P<more>[\w\W]*?)[\r\n ]*',
            r'\r\n{|\n\g<more>\r\n', new_table)
        # <table> tag with attributes, without more text on the same line
        new_table = re.sub(
            r'(?i)[\r\n]*?<##table## (?P<attr>[\w\W]*?)>[\r\n ]*',
            r'\r\n{| \g<attr>\r\n', new_table)
        # <table> tag without attributes, without more text on the same line
        new_table = re.sub(
            r'(?i)[\r\n]*?<##table##>[\r\n ]*', '\r\n{|\r\n', new_table)
        # end </table>
        new_table = re.sub(
            r'(?i)[\s]*<\/##table##>', '\r\n|}', new_table)

        ##################
        # caption with attributes
        new_table = re.sub(
            r'(?i)<caption (?P<attr>[\w\W]*?)>'
            r'(?P<caption>[\w\W]*?)<\/caption>',
            r'\r\n|+\g<attr> | \g<caption>', new_table)
        # caption without attributes
        new_table = re.sub(
            r'(?i)<caption>(?P<caption>[\w\W]*?)<\/caption>',
            r'\r\n|+ \g<caption>', new_table)

        ##################
        # <th> often people don't write them within <tr>, be warned!
        # <th> with attributes
        new_table = re.sub(
            r'(?i)[\r\n]+<th(?P<attr> [^>]*?)>(?P<header>[\w\W]*?)<\/th>',
            r'\r\n!\g<attr> | \g<header>\r\n', new_table)

        # <th> without attributes
        new_table = re.sub(
            r'(?i)[\r\n]+<th>(?P<header>[\w\W]*?)</th>',
            r'\r\n! \g<header>\r\n', new_table)

        # fail save. sometimes people forget </th>
        # <th> without attributes, without closing </th>
        new_table, n = re.subn(
            r'(?i)[\r\n]+<th>(?P<header>[\w\W]*?)[\r\n]+',
            r'\r\n! \g<header>\r\n', new_table)
        if n > 0:
            warning_messages.append(
                'WARNING: found <th> without </th>. ({} occurrences)\n'
                .format(n))
            warnings += n

        # <th> with attributes, without closing </th>
        new_table, n = re.subn(
            r'(?i)[\r\n]+<th(?P<attr> [^>]*?)>(?P<header>[\w\W]*?)[\r\n]+',
            r'\n!\g<attr> | \g<header>\r\n', new_table)
        if n > 0:
            warning_messages.append(
                'WARNING: found <th ...> without </th>. ({} occurrences\n)'
                .format(n))
            warnings += n

        ##################
        # <tr> with attributes
        new_table = re.sub(
            '(?i)[\r\n]*<tr(?P<attr> [^>]*?)>[\r\n]*',
            r'\r\n|-\g<attr>\r\n', new_table)

        # <tr> without attributes
        new_table = re.sub(
            '(?i)[\r\n]*<tr>[\r\n]*',
            r'\r\n|-\r\n', new_table)

        ##################
        # normal <td> without arguments
        new_table = re.sub(
            r'(?i)[\r\n]+<td>(?P<cell>[\w\W]*?)<\/td>',
            r'\r\n| \g<cell>\r\n', new_table)

        ##################
        # normal <td> with arguments
        new_table = re.sub(
            r'(?i)[\r\n]+<td(?P<attr> [^>]*?)>(?P<cell>[\w\W]*?)<\/td>',
            r'\r\n|\g<attr> | \g<cell>', new_table)

        # WARNING: this sub might eat cells of bad HTML, but most likely it
        # will correct errors
        # TODO: some more docu please
        new_table, n = re.subn(
            '(?i)[\r\n]+<td>(?P<cell>[^\r\n]*?)<td>',
            r'\r\n| \g<cell>\r\n', new_table)
        if n > 0:
            warning_messages.append(
                '<td> used where </td> was expected. ({} occurrences)\n'
                .format(n))
            warnings += n

        # what is this for?
        new_table, n = re.subn(
            r'[\r\n]+<(td|TD)([^>]+?)>([^\r\n]*?)</(td|TD)>',
            r'\r\n|\2 | \3\r\n', new_table)
        if n > 0:
            warning_messages.append(
                "WARNING: (sorry, bot code unreadable (1). I don't know why "
                'this warning is given.) ({} occurrences)\n'.format(n))

        # fail save. sometimes people forget </td>
        # <td> without arguments, with missing </td>
        new_table, n = re.subn(
            r'(?i)<td>(?P<cell>[^<]*?)[\r\n]+',
            r'\r\n| \g<cell>\r\n', new_table)
        if n > 0:
            warning_messages.append('NOTE: Found <td> without </td>. This '
                                    "shouldn't cause problems.\n")

        # <td> with attributes, with missing </td>
        new_table, n = re.subn(
            r'(?i)[\r\n]*<td(?P<attr> [^>]*?)>(?P<cell>[\w\W]*?)[\r\n]+',
            r'\r\n|\g<attr> | \g<cell>\r\n', new_table)
        if n > 0:
            warning_messages.append('NOTE: Found <td> without </td>. This '
                                    "shouldn't cause problems.\n")

        ##################
        # Garbage collecting ;-)
        new_table = re.sub(r'(?i)<td>[\r\n]*</tr>', '', new_table)
        # delete closing tags
        new_table = re.sub(r'(?i)[\r\n]*</t[rdh]>', '', new_table)

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
        new_table = re.sub(
            r"[\r\n]+\!([^'\n\r]*)'''([^'\r\n]*)'''",
            r'\r\n!\1\2', new_table)

        ##################
        # kills indentation within tables. Be warned, it might seldom bring
        # bad results.
        # True by default. Set 'deIndentTables = False' in user-config.py
        if config.deIndentTables:
            num = 1
            while num != 0:
                new_table, num = re.subn(
                    r'(\{\|[\w\W]*?)\n[ \t]+([\w\W]*?\|\})',
                    r'\1\r\n\2', new_table)

        ##################
        # kills additional spaces after | or ! or {|
        # This line was creating problems, so I commented it out --Daniel
        # newTable = re.sub("[\r\n]+\|[\t ]+?[\r\n]+", "\r\n| ", newTable)
        # kills trailing spaces and tabs
        new_table = re.sub(
            r'\r\n(.*)[\t ]+[\r\n]+', r'\r\n\1\r\n', new_table)
        # kill extra new-lines
        new_table = re.sub(r'[\r\n]{4,}[!|]', r'\r\n\1', new_table)

        ##################
        # shortening if <table> had no arguments/parameters
        new_table = re.sub(r'[\r\n]+{\| +\| ', r'\r\n{| ', new_table)
        # shortening if <td> had no articles
        new_table = re.sub(r'[\r\n]+\| +\| ', '\r\n| ', new_table)
        # shortening if <th> had no articles
        new_table = re.sub(r'\n\|\+ +\|', '\n|+ ', new_table)
        # shortening of <caption> had no articles
        new_table = re.sub(r'[\r\n]+! +\| ', '\r\n! ', new_table)

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
            new_table, num = re.subn(
                r'([\r\n]+(?:\|-|\{\|)[^\r\n\|]+) *= *([^"\s>]+)',
                r'\1="\2"', new_table, 1)

        num = 1
        while num != 0:
            # The same for header and cell tags ( ! or | ), but for these tags
            # the attribute part is finished by a | character. We don't want to
            # change cell contents which accidentally contain an equal sign.
            # Group 1 and 2 are anologously to the previous regular expression,
            # group 3 are the remaining attribute key - value pairs.
            new_table, num = re.subn(
                r'([\r\n]+(?:!|\|)[^\r\n\|]+) *= *([^"\s>]+)([^\|\r\n]*)\|',
                r'\1="\2"\3|', new_table, 1)

        ##################
        # merge two short <td>s
        num = 1
        while num != 0:
            new_table, num = re.subn(
                r'[\r\n]+(\|[^\|\-\}]{1}[^\n\r]{0,35})'
                r'[\r\n]+(\|[^\|\-\}]{1}[^\r\n]{0,35})[\r\n]+',
                r'\r\n\1 |\2\r\n', new_table)
        ####
        # add a new line if first is * or #
        new_table = re.sub(r'[\r\n]+\| ([*#]{1})', r'\r\n|\r\n\1', new_table)

        ##################
        # strip <center> from <th>
        new_table = re.sub(
            r'([\r\n]+![^\r\n]+?)<center>([\w\W]+?)</center>',
            r'\1 \2', new_table)
        # strip align="center" from <th> because the .css does it
        # if there are no other attributes than align, we don't need
        # that | either
        new_table = re.sub(
            r'([\r\n]+! +)align=\"center\" +\|', r'\1', new_table)
        # if there are other attributes, simply strip the align="center"
        new_table = re.sub(
            r'([\r\n]+![^\r\n|]+?)align=\"center\"([^\n\r|]+?\|)',
            r'\1 \2', new_table)

        ##################
        # kill additional spaces within arguments
        num = 1
        while num != 0:
            new_table, num = re.subn(
                r'[\r\n]+(\||\!)([^|\r\n]*?)[ \t]{2,}([^\r\n]+?)',
                r'\r\n\1\2 \3', new_table)

        ##################
        # I hate those long lines because they make a wall of letters
        # Off by default, set 'splitLongParagraphs = True' in user-config.py
        if config.splitLongParagraphs:
            num = 1
            while num != 0:
                # TODO: how does this work? docu please.
                # why are only äöüß used, but not other special characters?
                new_table, num = re.subn(
                    r'(\r\n[A-Z]{1}[^\n\r]{200,}?[a-zäöüß]\.)'
                    r'\ ([A-ZÄÖÜ]{1}[^\n\r]{200,})',
                    r'\1\r\n\2', new_table)
        return new_table, warnings, warning_messages

    def markActiveTables(self, text):
        """
        Mark all hidden table start and end tags.

        Mark all table start and end tags that are not disabled by nowiki tags,
        comments etc. We will then later only work on these marked tags.
        """
        exceptions = ['comment', 'math', 'nowiki', 'pre', 'syntaxhighlight']
        text = replaceExcept(text, _table_start_regex, '<##table##',
                             exceptions=exceptions)
        text = replaceExcept(text, _table_end_regex, '</##table##>',
                             exceptions=exceptions)
        return text

    def findTable(self, text):
        """
        Find the first HTML table (which can contain nested tables).

        Returns the table and the start and end position inside the text.
        """
        # Note that we added the ## characters in markActiveTables().
        m = _marked_table_start_search(text)
        if not m:
            return None, 0, 0

        start = m.start()
        offset = m.end()
        original_text = text
        text = text[m.end():]
        # depth level of table nesting
        depth = 1
        while depth > 0:
            next_starting = _marked_table_start_search(text)
            next_ending = _marked_table_end_search(text)
            if not next_ending:
                pywikibot.output(
                    'More opening than closing table tags. Skipping.')
                return None, 0, 0

            # if another table tag is opened before one is closed
            if next_starting and next_starting.start() < next_ending.start():
                offset += next_starting.end()
                text = text[next_starting.end():]
                depth += 1
            else:
                offset += next_ending.end()
                text = text[next_ending.end():]
                depth -= 1
        end = offset
        return original_text[start:end], start, end

    def convertAllHTMLTables(self, text):
        """
        Convert all HTML tables in text to wiki syntax.

        Returns the converted text, the number of converted tables and the
        number of warnings that occurred.
        """
        text = self.markActiveTables(text)

        converted_tables = 0
        warning_sum = 0
        warning_messages = ''

        while True:
            table, start, end = self.findTable(text)
            if not table:
                # no more HTML tables left
                break

            # convert the current table
            new_table, table_warns_num, table_warns = self.convertTable(table)
            warning_sum += table_warns_num
            for msg in table_warns:
                warning_messages += 'In table {}: {}'.format(
                    converted_tables + 1, msg)
            text = text[:start] + new_table + text[end:]
            converted_tables += 1

        pywikibot.output(warning_messages)
        return text, converted_tables, warning_sum

    def treat_page(self):
        """Convert all HTML tables in text to wiki syntax and save it."""
        text = self.current_page.text
        new_text, converted_tables, warnings = self.convertAllHTMLTables(text)

        # Check if there are any marked tags left
        if re.search('<##table##|</##table##>', new_text, re.IGNORECASE):
            pywikibot.error(
                'not all marked table start or end tags processed!')
            return

        if converted_tables == 0:
            pywikibot.output('No changes were necessary.')
            return

        if warnings:
            if self.opt.always and self.opt.skipwarning:
                pywikibot.output(
                    'There were {} replacements that might lead to bad '
                    'output. Skipping.'.format(warnings))
                return
            if not self.opt.always:
                pywikibot.output(
                    'There were {} replacements that might lead to bad '
                    'output.'.format(warnings))
                if not input_yn('Do you want to change the page anyway'):
                    return

        # get edit summary message
        if warnings == 0:
            edit_summary = i18n.twtranslate(
                self.site.code, 'table2wiki-no-warning')
        else:
            edit_summary = i18n.twntranslate(
                self.site.code,
                'table2wiki-warnings',
                {'count': warnings}
            )
        self.put_current(new_text, summary=edit_summary,
                         show_diff=not (self.opt.quiet
                                        and self.opt.always))


_marked_table_start_search = re.compile('<##table##', re.IGNORECASE).search
_marked_table_end_search = re.compile('</##table##>', re.IGNORECASE).search
_table_start_regex = re.compile('<table', re.IGNORECASE)
_table_end_regex = re.compile('</table>', re.IGNORECASE)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    :type args: str
    """
    options = {}
    gen = None

    local_args = pywikibot.handle_args(args)

    # This factory is responsible for processing command line arguments
    # that are also used by other scripts and that determine on which pages
    # to work on.
    gen_factory = pagegenerators.GeneratorFactory(positional_arg_name='page')

    for arg in local_args:
        option, _, value = arg.partition(':')
        if option == '-xml':
            filename = value or pywikibot.input(
                "Please enter the XML dump's filename:")
            gen = TableXmlDumpPageGenerator(filename)
        elif option in ['-always', '-quiet', '-skipwarning']:
            options[option[1:]] = True
        else:
            if option == '-mysqlquery':
                query = value or """
SELECT page_namespace, page_title
FROM page JOIN text ON (page_id = old_id)
WHERE old_text LIKE '%<table%'
"""
                arg = '-mysqlquery:' + query
            gen_factory.handle_arg(arg)

    if gen:
        gen = pagegenerators.NamespaceFilterPageGenerator(
            gen, gen_factory.namespaces)
    else:
        gen = gen_factory.getCombinedGenerator()

    if gen:
        if not gen_factory.nopreload:
            gen = pagegenerators.PreloadingGenerator(gen)
        bot = Table2WikiRobot(generator=gen, **options)
        bot.run()
    else:
        suggest_help(missing_generator=True)


if __name__ == '__main__':
    main()
