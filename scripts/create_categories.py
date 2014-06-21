# -*- coding: utf-8 -*-
"""
Program to batch create categories.

The program expects a generator containing a list of page titles to be used as
base.

The following command line parameters are supported:

-always         (not implemented yet) Don't ask, just do the edit.

-overwrite      (not implemented yet).

-parent         The name of the parent category.

-basename       The base to be used for the new category names.

Example:
create_categories.py
    -lang:commons
    -family:commons
    -links:User:Multichill/Wallonia
    -parent:"Cultural heritage monuments in Wallonia"
    -basename:"Cultural heritage monuments in"

"""
__version__ = '$Id$'
#
# (C) Multichill, 2011
# (C) xqt, 2011-2014
#
#   Distributed under the terms of the MIT license.
#
#
import pywikibot
from pywikibot import pagegenerators


def createCategory(page, parent, basename):
    title = page.title(withNamespace=False)

    newpage = pywikibot.Page(pywikibot.Site(u'commons', u'commons'),
                                 u'Category:' + basename + u' ' + title)
    newtext = u''
    newtext += u'[[Category:' + parent + u'|' + title + u']]\n'
    newtext += u'[[Category:' + title + u']]\n'

    if not newpage.exists():
        #FIXME: Add user prompting and -always option
        pywikibot.output(newpage.title())
        pywikibot.showDiff(u'', newtext)

        comment = u'Creating new category'
        try:
            newpage.put(newtext, comment)
        except pywikibot.EditConflict:
            pywikibot.output(u'Skipping %s due to edit conflict' % newpage.title())
        except pywikibot.ServerError:
            pywikibot.output(u'Skipping %s due to server error' % newpage.title())
        except pywikibot.PageNotSaved as error:
            pywikibot.output(u'Error putting page: %s' % error.args)
    else:
        #FIXME: Add overwrite option
        pywikibot.output(u'%s already exists, skipping' % newpage.title())


def main():
    '''
    Main loop. Get a generator and options.
    '''
    generator = None
    parent = u''
    basename = u''
    always = False

    # Process global args and prepare generator args parser
    local_args = pywikibot.handleArgs()
    genFactory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        if arg == '-always':
            always = True
        elif arg.startswith('-parent:'):
            parent = arg[len('-parent:'):].strip()
        elif arg.startswith('-basename'):
            basename = arg[len('-basename:'):].strip()
        else:
            genFactory.handleArg(arg)

    generator = genFactory.getCombinedGenerator()
    if generator:
        for page in generator:
            createCategory(page, parent, basename)
    else:
        pywikibot.output(u'No pages to work on')

    pywikibot.output(u'All done')

if __name__ == "__main__":
    main()
