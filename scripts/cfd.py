#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This script processes the Categories for discussion working page.

It parses out the actions that need to be taken as a result of CFD discussions
(as posted to the working page by an administrator) and performs them.

Syntax: python cfd.py

"""
#
# (C) Ben McIlwain, 2008
# (C) Pywikibot team, 2009-2013
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

import re
import pywikibot
from pywikibot import config2 as config
import category

# The location of the CFD working page.
cfdPage = u'Wikipedia:Categories for discussion/Working'

# A list of templates that are used on category pages as part of the CFD
# process that contain information such as the link to the per-day discussion page.
cfdTemplates = ['Cfd full', 'Cfr full']

# Regular expression declarations
# See the en-wiki CFD working page at [[Wikipedia:Categories for discussion/Working]]
# to see how these work in context.  To get this bot working on other wikis you will
# need to adjust these regular expressions at the very least.
nobots = re.compile(r"NO\s*BOTS", re.IGNORECASE)
example = re.compile(r"\[\[:Category:(.)\1\1\1\1\]\]", re.IGNORECASE)
speedymode = re.compile(r"^===*\s*Speedy Moves\s*===*\s*$", re.IGNORECASE)
movemode = re.compile(r"^===*\s*Move/Merge then delete\s*===*\s*$", re.IGNORECASE)
emptymode = re.compile(r"^===*\s*Empty then delete\s*===*\s*$", re.IGNORECASE)
deletemode = re.compile(r"^===*\s*Ready for deletion\s*===*\s*$", re.IGNORECASE)
maintenance = re.compile(r"^===*\s*Old by month categories with entries\s*===*\s*$", re.IGNORECASE)
dateheader = re.compile(r"(\[\[Wikipedia:Categories[_ ]for[_ ](?:discussion|deletion)/Log/([^\]]*?)\]\])",
                        re.IGNORECASE)
movecat = re.compile(r"\[\[:Category:([^\]]*?)\]\][^\]]*?\[\[:Category:([^\]]*?)\]\]", re.IGNORECASE)
deletecat = re.compile(r"\[\[:Category:([^\]]*?)\]\]", re.IGNORECASE)
findday = re.compile(r"\[\[(Wikipedia:Categories for (?:discussion|deletion)/Log/\d{4} \w+ \d+)#", re.IGNORECASE)


class ReCheck:

    """Helper class."""

    def __init__(self):
        self.result = None

    def check(self, pattern, text):
        self.result = pattern.search(text)
        return self.result


def main(*args):
    """
    Process command line arguments and perform task.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    pywikibot.handle_args(args)

    if config.family != 'wikipedia' or config.mylang != 'en':
        pywikibot.warning('CFD does work only on the English Wikipedia.')
        return

    page = pywikibot.Page(pywikibot.Site(), cfdPage)

    # Variable declarations
    day = "None"
    mode = "None"
    summary = ""
    robot = None

    m = ReCheck()
    for line in page.text.split("\n"):
        if nobots.search(line):
            # NO BOTS!!!
            pass
        elif example.search(line):
            # Example line
            pass
        elif speedymode.search(line):
            mode = "Speedy"
            day = "None"
        elif movemode.search(line):
            mode = "Move"
            day = "None"
        elif emptymode.search(line):
            mode = "Empty"
            day = "None"
        elif deletemode.search(line):
            mode = "Delete"
            day = "None"
        elif maintenance.search(line):
            # It's probably best not to try to handle these in an automated fashion.
            mode = "None"
            day = "None"
        elif m.check(dateheader, line):
            day = m.result.group(1)
            pywikibot.output("Found day header: %s" % day)
        elif m.check(movecat, line):
            src = m.result.group(1)
            dest = m.result.group(2)
            thisDay = findDay(src, day)
            if mode == "Move" and thisDay != "None":
                summary = "Robot - Moving category " + src + " to [[:Category:" + dest + "]] per [[WP:CFD|CFD]] at " + \
                          thisDay + "."
            elif mode == "Speedy":
                summary = "Robot - Speedily moving category " + src + " to [[:Category:" + dest + \
                          "]] per [[WP:CFDS|CFDS]]."
            else:
                continue
            # If the category is redirect, we do NOT want to move articles to
            # it. The safest thing to do here is abort and wait for human
            # intervention.
            destpage = pywikibot.Page(
                pywikibot.Site(), dest, ns=14)
            if destpage.isCategoryRedirect():
                summary = 'CANCELED. Destination is redirect: ' + summary
                pywikibot.output(summary, toStdout=True)
                robot = None
            else:
                robot = category.CategoryMoveRobot(oldcat=src, newcat=dest, batch=True,
                                                   comment=summary, inplace=True, move_oldcat=True,
                                                   delete_oldcat=True, deletion_comment=True)
        elif m.check(deletecat, line):
            src = m.result.group(1)
            # I currently don't see any reason to handle these two cases separately, though
            # if are guaranteed that the category in the "Delete" case is empty, it might be
            # easier to call delete.py on it.
            thisDay = findDay(src, day)
            if (mode == "Empty" or mode == "Delete") and thisDay != "None":
                summary = "Robot - Removing category " + src + " per [[WP:CFD|CFD]] at " + thisDay + "."
            else:
                continue
            robot = category.CategoryMoveRobot(oldcat=src, batch=True, comment=summary,
                                                 deletion_comment=True, inplace=True)
        else:
            # This line does not fit any of our regular expressions, so ignore it.
            pass
        if summary != "" and robot is not None:
            pywikibot.output(summary, toStdout=True)
            # Run, robot, run!
            robot.run()
        summary = ""
        robot = None


# This function grabs the wiki source of a category page and attempts to
# extract a link to the CFD per-day discussion page from the CFD template.
# If the CFD template is not there, it will return the value of the second
# parameter, which is essentially a fallback that is extracted from the
# per-day subheadings on the working page.
def findDay(pageTitle, oldDay):
    page = pywikibot.Page(pywikibot.Site(), u"Category:" + pageTitle)
    try:
        pageSrc = page.text
        m = findday.search(pageSrc)
    except pywikibot.NoPage:
        m = None

    if m is not None:
        return "[[" + m.group(1) + "]]"
    else:
        # Try to parse day link from CFD template parameters.
        templates = page.templatesWithParams()
        for template in templates:
            if template[0].title() in cfdTemplates:
                params = template[1]
                (day, month, year) = [None, None, None]
                for param in params:
                    (paramName, paramVal) = param.split('=', 1)
                    if paramName == 'day':
                        day = paramVal
                    elif paramName == 'month':
                        month = paramVal
                    elif paramName == 'year':
                        year = paramVal
                if day and month and year:
                    return "[[Wikipedia:Categories for discussion/Log/%s %s %s]]" % (year, month, day)
        return oldDay

if __name__ == "__main__":
    main()
