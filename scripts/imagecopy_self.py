# -*- coding: utf-8 -*-
"""
Script to copy self published files from English Wikipedia to Commons.

This bot is based on imagecopy.py and intended to be used to empty out
http://en.wikipedia.org/wiki/Category:Self-published_work

This bot uses a graphical interface and may not work from commandline
only environment.

Examples

Work on a single file:

    python pwb.py imagecopy.py -page:file:<filename>

Work on all images in a category:<cat>:

    python pwb.py imagecopy.py -cat:<cat>

Work on all images which transclude a template:

    python pwb.py imagecopy.py -transcludes:<template>

See pagegenerators.py for more ways to get a list of images.
By default the bot works on your home wiki (set in user-config)

This is a first test version and should be used with care.

Use -nochecktemplate if you don't want to add the check template. Be sure to
check it yourself.
"""
#
# Based on upload.py by:
# (C) Rob W.W. Hooft, Andre Engels 2003-2007
# (C) Wikipedian, Keichwa, Leogregianin, Rikwade, Misza13 2003-2007
#
# New bot by:
# (C) Kyle/Orgullomoore, Siebrand Mazeland 2007
#
# Another rewrite by:
# (C) Multichill 2008
#
# English Wikipedia specific bot by:
# (C) Multichill 2010-2012
#
# (C) Pywikibot team, 2010-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import re
import threading
import webbrowser

from datetime import datetime

import pywikibot

from pywikibot import pagegenerators, i18n

from pywikibot.specialbots import UploadRobot
from pywikibot.tools import PY2

from scripts import imagerecat, image

if not PY2:
    import tkinter as Tkinter

    from queue import Queue
else:
    import Tkinter

    from Queue import Queue

try:
    from pywikibot.userinterfaces.gui import Tkdialog
except ImportError as _tk_error:
    Tkdialog = object

NL = ''

nowCommonsTemplate = {
    'de': u'{{NowCommons|%s}}',
    'en': ('{{NowCommons|1=File:%s|date=~~~~~|'
           'reviewer={{subst:REVISIONUSER}}}}'),
    'lb': u'{{Elo op Commons|%s}}',
    'nds-nl': u'{{NoenCommons|1=File:%s}}',
    'shared': ('{{NowCommons|1=File:%s|date=~~~~~|'
               'reviewer={{subst:REVISIONUSER}}}}'),
}

moveToCommonsTemplate = {
    'de': ['NowCommons', 'NC', 'NCT', 'Nowcommons'],
    'en': [u'Commons ok', u'Copy to Wikimedia Commons', u'Move to commons',
           u'Movetocommons', u'To commons',
           u'Copy to Wikimedia Commons by BotMultichill'],
    'lb': [u'Move to commons'],
    'nds-nl': [u'Noar Commons', u'VNC'],
    'shared': [u'Move'],
}

skipTemplates = {
    'de': [u'Löschprüfung',
           u'NoCommons',
           u'NowCommons',
           u'NowCommons/Mängel',
           u'NowCommons-Überprüft',
           u'Wappenrecht',
           ],
    'en': [u'Db-f1',
           u'Db-f2',
           u'Db-f3',
           u'Db-f7',
           u'Db-f8',
           u'Db-f9',
           u'Db-f10',
           u'Do not move to Commons',
           u'NowCommons',
           u'CommonsNow',
           u'Nowcommons',
           u'NowCommonsThis',
           u'Nowcommons2',
           u'NCT',
           u'Nowcommonsthis',
           u'Moved to commons',
           u'Now Commons',
           u'Now at commons',
           u'Db-nowcommons',
           u'WikimediaCommons',
           u'Now commons',
           u'Di-no source',
           u'Di-no license',
           u'Di-no permission',
           u'Di-orphaned fair use',
           u'Di-no source no license',
           u'Di-replaceable fair use',
           u'Di-no fair use rationale',
           u'Di-disputed fair use rationale',
           u'Puf',
           u'PUI',
           u'Pui',
           u'Ffd',
           u'PD-user',  # Only the self templates are supported for now.
           u'Ticket Scan',
           u'Non-free 2D art',
           u'Non-free 3D art',
           u'Non-free architectural work',
           u'Non-free fair use in',
           ],
    'lb': [u'Läschen',
           ],
    'nds-nl': [u'Allinnig Wikipedie',
               u'Bepark',
               u'Gienidee',
               u'NoenCommons',
               u'NowCommons',
               ],
    'shared': [u''],
}


licenseTemplates = {
    'de': [
        (r'\{\{Bild-CC-by-sa/3\.0/de\}\}[\s\r\n]*\{\{Bild-CC-by-sa/3\.0\}\}'
         r'[\s\r\n]*\{\{Bild-GFDL-Neu\}\}',
         '{{Self|Cc-by-sa-3.0-de|Cc-by-sa-3.0|GFDL|author='
         '[[:%(lang)s:User:%(author)s|%(author)s]] at [http://%(lang)s.%'
         '(family)s.org %(lang)s.%(family)s]}}'),
        (r'\{\{Bild-GFDL\}\}[\s\r\n]*\{\{Bild-CC-by-sa/(\d\.\d)\}\}',
         r'{{Self|GFDL|Cc-by-sa-3.0-migrated|Cc-by-sa-\1|author='
         '[[:%(lang)s:User:%(author)s|%(author)s]] at '
         '[http://%(lang)s.%(family)s.org %(lang)s.%(family)s]}}'),
        (r'\{\{Bild-GFDL\}\}',
         '{{Self|GFDL|Cc-by-sa-3.0-migrated|author='
         '[[:%(lang)s:User:%(author)s|%(author)s]] at '
         '[http://%(lang)s.%(family)s.org %(lang)s.%(family)s]}}'),
        (r'\{\{Bild-CC-by-sa/(\d\.\d)\}\}',
         r'{{Self|Cc-by-sa-\1|author=[[:%(lang)s:User:%(author)s|%(author)s]] '
         'at [http://%(lang)s.%(family)s.org %(lang)s.%(family)s]}}'),
        (r'\{\{Bild-CC-by-sa/(\d\.\d)/de\}\}',
         r'{{Self|Cc-by-sa-\1-de|author='
         '[[:%(lang)s:User:%(author)s|%(author)s]] at '
         '[http://%(lang)s.%(family)s.org %(lang)s.%(family)s]}}'),
        (r'\{\{Bild-CC-by/(\d\.\d)\}\}',
         r'{{Self|Cc-by-\1|author=[[:%(lang)s:User:%(author)s|%(author)s]] at '
         '[http://%(lang)s.%(family)s.org %(lang)s.%(family)s]}}'),
        (r'\{\{Bild-CC-by/(\d\.\d)/de\}\}',
         r'{{Self|Cc-by-\1-de|author=[[:%(lang)s:User:%(author)s|%(author)s]] '
         'at [http://%(lang)s.%(family)s.org %(lang)s.%(family)s]}}'),
    ],
    'en': [
        (r'\{\{(self|self2)\|([^\}]+)\}\}',
         r'{{Self|\2|author=[[:%(lang)s:User:%(author)s|%(author)s]] at '
         '[http://%(lang)s.%(family)s.org %(lang)s.%(family)s]}}'),
        (r'\{\{(GFDL-self|GFDL-self-no-disclaimers)\|([^\}]+)\}\}',
         r'{{Self|GFDL|\2|author=[[:%(lang)s:User:%(author)s|%(author)s]] at '
         '[http://%(lang)s.%(family)s.org %(lang)s.%(family)s]}}'),
        (r'\{\{GFDL-self-with-disclaimers\|([^\}]+)\}\}',
         r'{{Self|GFDL-with-disclaimers|\1|author='
         '[[:%(lang)s:User:%(author)s|%(author)s]] at '
         '[http://%(lang)s.%(family)s.org %(lang)s.%(family)s]}}'),
        (r'\{\{PD-self(\|date=[^\}]+)?\}\}',
         '{{PD-user-w|%(lang)s|%(family)s|%(author)s}}'),
        (r'\{\{Multilicense replacing placeholder'
         r'(\|[^\}\|=]+=[^\}\|]+)*(?P<migration>\|[^\}\|=]+=[^\}\|]+)'
         r'(\|[^\}\|=]+=[^\}\|]+)*\}\}',
         r'{{Self|GFDL|Cc-by-sa-2.5,2.0,1.0\g<migration>|author='
         '[[:%(lang)s:User:%(author)s|%(author)s]] at '
         '[http://%(lang)s.%(family)s.org %(lang)s.%(family)s]}}'),
        (r'\{\{Multilicense replacing placeholder new(\|class=[^\}]+)?\}\}',
         '{{Self|GFDL|Cc-by-sa-3.0,2.5,2.0,1.0|author='
         '[[:%(lang)s:User:%(author)s|%(author)s]] at'
         '[http://%(lang)s.%(family)s.org %(lang)s.%(family)s]}}'),
    ],
    'lb': [
        (r'\{\{(self|self2)\|([^\}]+)\}\}',
         r'{{Self|\2|author='
         '[[:%(lang)s:User:%(author)s|%(author)s]] at '
         '[http://%(lang)s.%(family)s.org %(lang)s.%(family)s]}}'),
    ],
    'nds-nl': [
        (r'\{\{PD-eigenwark\}\}',
         '{{PD-user-w|%(lang)s|%(family)s|%(author)s}}'),
    ],
    'shared': [
        (r'\{\{(self|self2)\|([^\}]+)\}\}',
         r'{{Self|\2|author=%(author)s at old wikivoyage shared}}'),
    ],
}

sourceGarbage = {
    'de': [r'==\s*Beschreibung,\sQuelle\s*==',
           r'==\s*Beschrieving\s*==',
           r'==\s*\[\[Wikipedia:Lizenzvorlagen für Bilder\|Lizenz\]\]\s*==',
           ],
    'en': [r'==\s*Description\s*==',
           r'==\s*Summary\s*==',
           r'==\s*Licensing:?\s*==',
           r'\{\{'
           '(Copy to Wikimedia Commons|Move to Commons|Move to commons|'
           'Move to Wikimedia Commons|Copy to commons|Mtc|MtC|MTC|CWC|CtWC|'
           'CTWC|Ctwc|Tocommons|Copy to Commons|To Commons|Movetocommons|'
           'Move to Wikimedia commons|Move-to-commons|Commons ok|ToCommons|'
           'To commons|MoveToCommons|Copy to wikimedia commons|'
           'Upload to commons|CopyToCommons|Copytocommons|MITC|MovetoCommons|'
           'Do move to Commons|Orphan image)'
           r'(\|[^\}]+)?\}\}'
           ],
    'lb': [r'==\s*Résumé\s*==',
           r'==\s*Lizenz:\s*==',
           ],
    'nds-nl': [r'==\s*Licentie\s*==',
               r'\{\{DEFAULTSORT:\{\{PAGENAME\}\}\}\}',
               ],
    'shared': [r'==\s*Beschreibung,\sQuelle\s*==',
               r'==\s*Licensing:?\s*==',
               ],
}

informationTemplate = {
    'de': 'Information',
    'en': 'Information',
    'lb': 'Information',
    'nds-nl': 'Information',
    'shared': 'Information',
}

informationFields = {
    'de': {
        u'anmerkungen': u'remarks',  # FIXME: More flexible
        u'beschreibung': u'description',
        u'quelle': u'source',
        u'datum': u'date',
        u'urheber': u'author',
        u'permission': u'permission',
        u'andere Versione': u'other versions',
    },
    'en': {
        u'location': u'remarks',
        u'description': u'description',
        u'source': u'source',
        u'date': u'date',
        u'author': u'author',
        u'permission': u'permission',
        u'other versions': u'other versions',
    },
    'lb': {
        u'location': u'remarks',
        u'description': u'description',
        u'source': u'source',
        u'date': u'date',
        u'author': u'author',
        u'permission': u'permission',
        u'other versions': u'other versions',
    },
    'nds-nl': {
        u'location': u'remarks',
        u'description': u'description',
        u'source': u'source',
        u'date': u'date',
        u'author': u'author',
        u'permission': u'permission',
        u'other versions': u'other versions',
    },
    'shared': {
        u'description': u'description',
        u'source': u'source',
        u'date': u'date',
        u'author': u'author',
        u'permission': u'permission',
        u'other versions': u'other versions',
    },
}


def supportedSite():
    """Check if this site is supported."""
    site = pywikibot.Site()
    lang = site.code

    lists = [
        nowCommonsTemplate,
        moveToCommonsTemplate,
        skipTemplates,
        licenseTemplates,
        sourceGarbage,
        informationTemplate,
        informationFields,
    ]
    for l in lists:
        if not l.get(lang):
            return False
    return True


class imageFetcher(threading.Thread):

    """Tries to fetch information for all images in the generator."""

    def __init__(self, pagegenerator, prefetchQueue):
        """Constructor."""
        self.pagegenerator = pagegenerator
        self.prefetchQueue = prefetchQueue
        imagerecat.initLists()
        threading.Thread.__init__(self)

    def run(self):
        """Run imageFetcher."""
        for page in self.pagegenerator:
            self.processImage(page)
        self.prefetchQueue.put(None)
        pywikibot.output('Fetched all images.')
        return True

    def processImage(self, page):
        """Work on a single image."""
        if page.exists() and (page.namespace() == 6) and \
           (not page.isRedirectPage()):
            imagepage = pywikibot.FilePage(page.site(), page.title())

            # First do autoskip.
            if self.doiskip(imagepage):
                pywikibot.output(
                    u'Skipping %s : Got a template on the skip list.'
                    % page.title())
                return False

            text = imagepage.get()
            foundMatch = False
            for (regex, replacement) in licenseTemplates[page.site.lang]:
                match = re.search(regex, text, flags=re.IGNORECASE)
                if match:
                    foundMatch = True
            if not foundMatch:
                pywikibot.output(
                    u'Skipping %s : No suitable license template was found.'
                    % page.title())
                return False
            self.prefetchQueue.put(self.getNewFields(imagepage))

    def doiskip(self, imagepage):
        """Skip this image or not.

        Returns True if the image is on the skip list, otherwise False

        """
        for template in imagepage.templates():
            if template in skipTemplates[imagepage.site.lang]:
                pywikibot.output(
                    u'Found %s which is on the template skip list' % template)
                return True
        return False

    def getNewFields(self, imagepage):
        """Build a new description based on the imagepage."""
        if u'{{Information' in imagepage.get() or \
           u'{{information' in imagepage.get():
            (description, date, source, author, permission,
             other_versions) = self.getNewFieldsFromInformation(imagepage)
        else:
            (description, date, source,
             author) = self.getNewFieldsFromFreetext(imagepage)
            permission = u''
            other_versions = u''

        licensetemplate = self.getNewLicensetemplate(imagepage)
        categories = self.getNewCategories(imagepage)
        return {u'imagepage': imagepage,
                u'filename': imagepage.title(withNamespace=False),
                u'description': description,
                u'date': date,
                u'source': source,
                u'author': author,
                u'permission': permission,
                u'other_versions': other_versions,
                u'licensetemplate': licensetemplate,
                u'categories': categories,
                u'skip': False}

    def getNewFieldsFromInformation(self, imagepage):
        """Extract fields from current information template for new template.

        @param imagepage: The file page to get the template.
        @type imagepage: pywikibot.FilePage
        """
        # fields = ['location', 'description', 'source', 'date', 'author',
        #           'permission', 'other versions']
        # FIXME: The implementation for German has to be checked for the
        #        "strange" fields

        description = u''
        source = u''
        date = u''
        author = u''
        permission = u''
        other_versions = u''
        contents = {}

        for key, value in informationFields[imagepage.site.lang].items():
            contents[value] = u''

        templates = imagepage.templatesWithParams()
        information = informationTemplate[imagepage.site.lang]
        fields = informationFields[imagepage.site.lang]

        for (template, params) in templates:
            if template == information:
                for param in params:
                    # Split at =
                    (field, sep, value) = param.partition(u'=')
                    # To lowercase, remove underscores and strip of spaces
                    field = field.lower().replace(u'_', u' ').strip()
                    key = fields.get(field)
                    # See if first part is in fields list
                    if key:
                        # Ok, field is good, store it.
                        contents[key] = value.strip()

        # We now got the contents from the old information template.
        # Let's get the info for the new one

        # Description
        # FIXME: Add {{<lang>|<original text>}} if <lang is valid at Commons
        if contents[u'description']:
            description = self.convertLinks(contents[u'description'],
                                            imagepage.site())
        if contents.get(u'remarks') and contents[u'remarks']:
            if description == u'':
                description = self.convertLinks(contents[u'remarks'],
                                                imagepage.site())
            else:
                description += u'<BR/>\n' + self.convertLinks(
                    contents[u'remarks'], imagepage.site())

        # Source
        source = self.getSource(imagepage,
                                source=self.convertLinks(contents[u'source'],
                                                         imagepage.site()))

        # Date
        if contents[u'date']:
            date = contents[u'date']
        else:
            date = self.getUploadDate(imagepage)

        # Author
        if not (contents[u'author'] == u'' or
                contents[u'author'] == self.getAuthor(imagepage)):
            author = self.convertLinks(contents[u'author'], imagepage.site())
        else:
            author = self.getAuthorText(imagepage)

        # Permission
        # Still have to filter out crap like "see below" or "yes"
        if contents[u'permission']:
            # Strip of the license temlate if it's in the permission section
            for (regex, repl) in licenseTemplates[imagepage.site.lang]:
                contents[u'permission'] = re.sub(regex, u'',
                                                 contents[u'permission'],
                                                 flags=re.IGNORECASE)
            permission = self.convertLinks(contents[u'permission'],
                                           imagepage.site())

        # Other_versions
        if contents[u'other versions']:
            other_versions = self.convertLinks(contents[u'other versions'],
                                               imagepage.site())

        return (description, date, source, author, permission, other_versions)

    def getNewFieldsFromFreetext(self, imagepage):
        """Extract fields from free text for the new information template."""
        text = imagepage.get()
        # text = re.sub(u'== Summary ==', u'', text, re.IGNORECASE)
        # text = re.sub(u'== Licensing ==', u'', text, re.IGNORECASE)
        # text = re.sub('\{\{(self|self2)\|[^\}]+\}\}', '', text, re.IGNORECASE)

        for toRemove in sourceGarbage[imagepage.site.lang]:
            text = re.sub(toRemove, u'', text, flags=re.IGNORECASE)

        for (regex, repl) in licenseTemplates[imagepage.site.lang]:
            text = re.sub(regex, u'', text, flags=re.IGNORECASE)

        text = pywikibot.removeCategoryLinks(text, imagepage.site()).strip()

        description = self.convertLinks(text.strip(), imagepage.site())
        date = self.getUploadDate(imagepage)
        source = self.getSource(imagepage)
        author = self.getAuthorText(imagepage)
        return (description, date, source, author)

    def getUploadDate(self, imagepage):
        """Get the original upload date for usage.

        The date is put in the date field of the new
        information template. If we really have nothing better.

        """
        uploadtime = imagepage.getFileVersionHistory()[-1][0]
        uploadDatetime = datetime.strptime(uploadtime, u'%Y-%m-%dT%H:%M:%SZ')
        return (u'{{Date|' + str(uploadDatetime.year) + u'|' +
                str(uploadDatetime.month) + u'|' + str(uploadDatetime.day) +
                u'}} (original upload date)')

    def getSource(self, imagepage, source=u''):
        """Get text to put in the source field of new information template."""
        site = imagepage.site()
        lang = site.code
        family = site.family.name
        if source == u'':
            source = u'{{Own}}'

        return (source.strip() +
                '<BR />Transferred from [http://%(lang)s.%(family)s.org '
                '%(lang)s.%(family)s]') % {u'lang': lang, u'family': family}

    def getAuthorText(self, imagepage):
        """Get uploader to put in the author field of information template."""
        site = imagepage.site()
        lang = site.code
        family = site.family.name

        firstuploader = self.getAuthor(imagepage)
        return ('[[:%(lang)s:User:%(firstuploader)s|%(firstuploader)s]] at '
                '[http://%(lang)s.%(family)s.org %(lang)s.%(family)s]'
                % {u'lang': lang, u'family': family,
                   u'firstuploader': firstuploader})

    def getAuthor(self, imagepage):
        """Get the first uploader."""
        return imagepage.getFileVersionHistory()[-1][1].strip()

    def convertLinks(self, text, sourceSite):
        """Convert links from the current wiki to Commons."""
        lang = sourceSite.code
        family = sourceSite.family.name
        conversions = [
            (r'\[\[([^\[\]\|]+)\|([^\[\]\|]+)\]\]', r'[[:%(lang)s:\1|\2]]'),
            (r'\[\[([^\[\]\|]+)\]\]', r'[[:%(lang)s:\1|\1]]'),
        ]
        for (regex, replacement) in conversions:
            text = re.sub(regex, replacement % {u'lang': lang,
                                                u'family': family}, text)
        return text

    def getNewLicensetemplate(self, imagepage):
        """Get a license template to put on the image to be uploaded."""
        text = imagepage.get()
        site = imagepage.site()
        lang = site.code
        family = site.family.name
        result = u''
        for (regex,
             replacement) in licenseTemplates[imagepage.site.lang]:
            match = re.search(regex, text, flags=re.IGNORECASE)
            if match:
                result = re.sub(regex, replacement, match.group(0),
                                flags=re.IGNORECASE)
                return result % {u'author': self.getAuthor(imagepage),
                                 u'lang': lang,
                                 u'family': family}
        return result

    def getNewCategories(self, imagepage):
        """Get categories for the image.

        Don't forget to filter.

        """
        result = u''
        (commonshelperCats, usage,
         galleries) = imagerecat.getCommonshelperCats(imagepage)
        newcats = imagerecat.applyAllFilters(commonshelperCats)
        for newcat in newcats:
            result += u'[[Category:' + newcat + u']] '
        return result


class userInteraction(threading.Thread):

    """Prompt all images to the user."""

    def __init__(self, prefetchQueue, uploadQueue):
        """Constructor."""
        self.prefetchQueue = prefetchQueue
        self.uploadQueue = uploadQueue
        self.autonomous = False
        threading.Thread.__init__(self)

    def run(self):
        """Run thread."""
        while True:
            fields = self.prefetchQueue.get()
            if fields:
                self.processImage(fields)
            else:
                break
        self.uploadQueue.put(None)
        pywikibot.output('User worked on all images.')
        return True

    def setAutonomous(self):
        """Don't do any user interaction."""
        self.autonomous = True
        return

    def processImage(self, fields):
        """Work on a single image."""
        if self.autonomous:
            # Check if the image already exists. Do nothing if the name is
            # already taken.
            CommonsPage = pywikibot.Page(pywikibot.Site('commons',
                                                        'commons'),
                                         u'File:' + fields.get('filename'))
            if CommonsPage.exists():
                return False
        else:
            while True:
                # Do the TkdialogICS to accept/reject and change te name
                fields = TkdialogICS(fields).getnewmetadata()

                if fields.get('skip'):
                    pywikibot.output(u'Skipping %s : User pressed skip.'
                                     % fields.get('imagepage').title())
                    return False

                # Check if the image already exists
                CommonsPage = pywikibot.Page(pywikibot.Site('commons',
                                                            'commons'),
                                             u'File:' + fields.get('filename'))
                if not CommonsPage.exists():
                    break
                else:
                    pywikibot.output('Image already exists, pick another name '
                                     'or skip this image')
                    # We dont overwrite images, pick another name, go to the
                    # start of the loop

        # Put the fields in the queue to be uploaded
        self.uploadQueue.put(fields)


class TkdialogICS(Tkdialog):

    """The dialog window for image info."""

    def __init__(self, fields):
        """Constructor.

        fields:
            imagepage, description, date, source, author, licensetemplate,
            categories
        """
        """Constructor."""
        self.root = Tkinter.Tk()
        # "%dx%d%+d%+d" % (width, height, xoffset, yoffset)
        # Always appear the same size and in the bottom-left corner
        # FIXME : Base this on the screen size or make it possible for the user
        # to configure this

        # Get all the relevant fields
        super(TkdialogICS, self).__init__()
        self.imagepage = fields.get('imagepage')
        self.filename = fields.get('filename')

        self.description = fields.get('description')
        self.date = fields.get('date')
        self.source = fields.get('source')
        self.author = fields.get('author')
        self.permission = fields.get('permission')
        self.other_versions = fields.get('other_versions')

        self.licensetemplate = fields.get('licensetemplate')
        self.categories = fields.get('categories')
        self.skip = False

        # Start building the page
        self.root.geometry("1500x400+100-100")
        self.root.title(self.filename)

        self.url = self.imagepage.permalink()
        self.scrollbar = Tkinter.Scrollbar(self.root, orient=Tkinter.VERTICAL)

        self.old_description = Tkinter.Text(self.root)
        self.old_description.insert(Tkinter.END,
                                    self.imagepage.get().encode('utf-8'))
        self.old_description.config(state=Tkinter.DISABLED,
                                    height=8, width=140, padx=0, pady=0,
                                    wrap=Tkinter.WORD,
                                    yscrollcommand=self.scrollbar.set)

        self.scrollbar.config(command=self.old_description.yview)

        self.old_description_label = Tkinter.Label(
            self.root, text='The old description was : ')
        self.new_description_label = Tkinter.Label(
            self.root, text='The new fields are : ')
        self.filename_label = Tkinter.Label(self.root, text=u'Filename : ')
        self.information_description_label = Tkinter.Label(
            self.root, text='Description : ')
        self.information_date_label = Tkinter.Label(self.root, text=u'Date : ')
        self.information_source_label = Tkinter.Label(self.root,
                                                      text='Source : ')
        self.information_author_label = Tkinter.Label(self.root,
                                                      text='Author : ')
        self.information_permission_label = Tkinter.Label(self.root,
                                                          text='Permission : ')
        self.information_other_versions_label = Tkinter.Label(
            self.root, text='Other versions : ')

        self.information_licensetemplate_label = Tkinter.Label(
            self.root, text='License : ')
        self.information_categories_label = Tkinter.Label(
            self.root, text=u'Categories : ')

        self.filename_field = Tkinter.Entry(self.root)
        self.information_description = Tkinter.Entry(self.root)
        self.information_date = Tkinter.Entry(self.root)
        self.information_source = Tkinter.Entry(self.root)
        self.information_author = Tkinter.Entry(self.root)
        self.information_permission = Tkinter.Entry(self.root)
        self.information_other_versions = Tkinter.Entry(self.root)
        self.information_licensetemplate = Tkinter.Entry(self.root)
        self.information_categories = Tkinter.Entry(self.root)

        self.field_width = 120

        self.filename_field.config(width=self.field_width)
        self.information_description.config(width=self.field_width)
        self.information_date.config(width=self.field_width)
        self.information_source.config(width=self.field_width)
        self.information_author.config(width=self.field_width)
        self.information_permission.config(width=self.field_width)
        self.information_other_versions.config(width=self.field_width)
        self.information_licensetemplate.config(width=self.field_width)
        self.information_categories.config(width=self.field_width)

        self.filename_field.insert(0, self.filename)
        self.information_description.insert(0, self.description)
        self.information_date.insert(0, self.date)
        self.information_source.insert(0, self.source)
        self.information_author.insert(0, self.author)
        self.information_permission.insert(0, self.permission)
        self.information_other_versions.insert(0, self.other_versions)
        self.information_licensetemplate.insert(0, self.licensetemplate)
        self.information_categories.insert(0, self.categories)

        self.browser_button = Tkinter.Button(self.root,
                                             text='View in browser',
                                             command=self.open_in_browser)
        self.skip_button = Tkinter.Button(self.root, text='Skip',
                                          command=self.skipFile)
        self.ok_button = Tkinter.Button(self.root, text='OK',
                                        command=self.ok_file)

        # Start grid
        self.old_description_label.grid(row=0, column=0, columnspan=3)

        self.old_description.grid(row=1, column=0, columnspan=3)
        self.scrollbar.grid(row=1, column=3)
        self.new_description_label.grid(row=2, column=0, columnspan=3)

        # All the labels for the new fields
        self.filename_label.grid(row=3, column=0)
        self.information_description_label.grid(row=4, column=0)
        self.information_date_label.grid(row=5, column=0)
        self.information_source_label.grid(row=6, column=0)
        self.information_author_label.grid(row=7, column=0)
        self.information_permission_label.grid(row=8, column=0)
        self.information_other_versions_label.grid(row=9, column=0)
        self.information_licensetemplate_label.grid(row=10, column=0)
        self.information_categories_label.grid(row=11, column=0)

        # The new fields
        self.filename_field.grid(row=3, column=1, columnspan=3)
        self.information_description.grid(row=4, column=1, columnspan=3)
        self.information_date.grid(row=5, column=1, columnspan=3)
        self.information_source.grid(row=6, column=1, columnspan=3)
        self.information_author.grid(row=7, column=1, columnspan=3)
        self.information_permission.grid(row=8, column=1, columnspan=3)
        self.information_other_versions.grid(row=9, column=1, columnspan=3)
        self.information_licensetemplate.grid(row=10, column=1, columnspan=3)
        self.information_categories.grid(row=11, column=1, columnspan=3)

        # The buttons at the bottom
        self.ok_button.grid(row=12, column=3, rowspan=2)
        self.skip_button.grid(row=12, column=2, rowspan=2)
        self.browser_button.grid(row=12, column=1, rowspan=2)

    def ok_file(self):
        """The user pressed the OK button."""
        self.filename = self.filename_field.get()
        self.description = self.information_description.get()
        self.date = self.information_date.get()
        self.source = self.information_source.get()
        self.author = self.information_author.get()
        self.permission = self.information_permission.get()
        self.other_versions = self.information_other_versions.get()
        self.licensetemplate = self.information_licensetemplate.get()
        self.categories = self.information_categories.get()

        self.root.destroy()

    def getnewmetadata(self):
        """Activate dialog and return new name and if the image is skipped."""
        self.root.mainloop()

        return {u'imagepage': self.imagepage,
                u'filename': self.filename,
                u'description': self.description,
                u'date': self.date,
                u'source': self.source,
                u'author': self.author,
                u'permission': self.permission,
                u'other_versions': self.other_versions,
                u'licensetemplate': self.licensetemplate,
                u'categories': self.categories,
                u'skip': self.skip}

    def open_in_browser(self):
        """The user pressed the View in browser button."""
        webbrowser.open(self.url)


class uploader(threading.Thread):

    """Upload all images."""

    def __init__(self, uploadQueue):
        """Constructor."""
        self.uploadQueue = uploadQueue
        self.checktemplate = True
        threading.Thread.__init__(self)

    def run(self):
        """Run uploader."""
        while True:  # Change later
            fields = self.uploadQueue.get()
            if fields:
                self.processImage(fields)
            else:
                break
        return True

    def nochecktemplate(self):
        """Don't want to add {{BotMoveToCommons}}."""
        self.checktemplate = False
        return

    def processImage(self, fields):
        """Work on a single image."""
        cid = self.buildNewImageDescription(fields)
        pywikibot.output(cid)
        bot = UploadRobot(url=fields.get('imagepage').fileUrl(),
                          description=cid,
                          useFilename=fields.get('filename'),
                          keepFilename=True, verifyDescription=False,
                          ignoreWarning=True,
                          targetSite=pywikibot.Site('commons', 'commons'))
        bot.run()

        self.tagNowcommons(fields.get('imagepage'), fields.get('filename'))
        self.replaceUsage(fields.get('imagepage'), fields.get('filename'))

    def buildNewImageDescription(self, fields):
        """Build a new information template."""
        site = fields.get('imagepage').site()
        lang = site.code
        family = site.family.name

        cid = u''
        if self.checktemplate:
            cid += ('\n{{BotMoveToCommons|%(lang)s.%(family)s'
                    '|year={{subst:CURRENTYEAR}}'
                    '|month={{subst:CURRENTMONTHNAME}}'
                    '|day={{subst:CURRENTDAY}}}}\n'
                    % {'lang': lang, 'family': family}
                    )
        cid += u'== {{int:filedesc}} ==\n'
        cid += u'{{Information\n'
        cid += u'|description=%(description)s\n' % fields
        cid += u'|date=%(date)s\n' % fields
        cid += u'|source=%(source)s\n' % fields
        cid += u'|author=%(author)s\n' % fields
        cid += u'|permission=%(permission)s\n' % fields
        cid += u'|other_versions=%(other_versions)s\n' % fields
        cid += u'}}\n'
        cid += u'== {{int:license}} ==\n'
        cid += u'%(licensetemplate)s\n' % fields
        cid += u'\n'
        cid += self.getOriginalUploadLog(fields.get('imagepage'))
        cid += u'__NOTOC__\n'
        if fields.get('categories').strip() == u'':
            cid = cid + u'{{Subst:Unc}}'
        else:
            cid = cid + u'%(categories)s\n' % fields
        return cid

    def getOriginalUploadLog(self, imagepage):
        """Get upload log to put at the bottom of the image description page.

        @param imagepage: The file page to retrieve the log.
        @type imagepage: pywikibot.FilePage
        """
        filehistory = imagepage.getFileVersionHistory()
        filehistory.reverse()

        site = imagepage.site()
        lang = site.code
        family = site.family.name

        sourceimage = imagepage.site.get_address(
            imagepage.title()).replace(u'&redirect=no&useskin=monobook', u'')

        result = u'== {{Original upload log}} ==\n'
        result += ('The original description page is/was '
                   '[http://%(lang)s.%(family)s.org%(sourceimage)s here]. '
                   'All following user names refer to %(lang)s.%(family)s.\n'
                   % {u'lang': lang, u'family': family,
                      u'sourceimage': sourceimage})
        for (timestamp, username, resolution, size, comment) in filehistory:
            date = datetime.strptime(
                timestamp, u'%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d %H:%M')
            result += (
                '* %(date)s [[:%(lang)s:user:%(username)s|%(username)s]] '
                "%(resolution)s (%(size)s bytes) ''"
                "<nowiki>%(comment)s</nowiki>''\n" % {
                    'lang': lang,
                    'family': family,
                    'date': date,
                    'username': username,
                    'resolution': resolution,
                    'size': size,
                    'comment': comment})

        return result

    def tagNowcommons(self, imagepage, filename):
        """Tagged the imag which has been moved to Commons for deletion."""
        if pywikibot.Page(pywikibot.Site('commons', 'commons'),
                          u'File:' + filename).exists():
            # Get a fresh copy, force to get the page so we dont run into edit
            # conflicts
            imtxt = imagepage.get(force=True)

            # Remove the move to commons templates
            if imagepage.site.lang in moveToCommonsTemplate:
                for moveTemplate in moveToCommonsTemplate[
                        imagepage.site.lang]:
                    imtxt = re.sub(r'(?i){{' + moveTemplate +
                                   r'[^}]*}}', r'', imtxt)

            # add {{NowCommons}}
            if imagepage.site.lang in nowCommonsTemplate:
                addTemplate = nowCommonsTemplate[
                    imagepage.site.lang] % filename
            else:
                addTemplate = nowCommonsTemplate['_default'] % filename

            commentText = i18n.twtranslate(
                imagepage.site(), 'commons-file-now-available',
                {'localfile': imagepage.title(withNamespace=False),
                 'commonsfile': filename})

            pywikibot.showDiff(imagepage.get(), imtxt + addTemplate)
            imagepage.put(imtxt + addTemplate, comment=commentText)

    def replaceUsage(self, imagepage, filename):
        """Replace all usage if image is uploaded under a different name."""
        if imagepage.title(withNamespace=False) != filename:
            gen = pagegenerators.FileLinksGenerator(imagepage)
            preloadingGen = pagegenerators.PreloadingGenerator(gen)

            moveSummary = i18n.twtranslate(
                imagepage.site(), 'commons-file-moved',
                {'localfile': imagepage.title(withNamespace=False),
                 'commonsfile': filename})

            imagebot = image.ImageRobot(
                generator=preloadingGen,
                oldImage=imagepage.title(withNamespace=False),
                newImage=filename, summary=moveSummary,
                always=True, loose=True)
            imagebot.run()


def main(*args):
    """Process command line arguments and invoke bot."""
    autonomous = False
    checkTemplate = True

    # Load a lot of default generators
    genFactory = pagegenerators.GeneratorFactory()
    local_args = pywikibot.handle_args(args)
    for arg in local_args:
        if arg == '-nochecktemplate':
            checkTemplate = False
        elif arg == '-autonomous':
            autonomous = True
        else:
            genFactory.handleArg(arg)

    pregenerator = genFactory.getCombinedGenerator(preload=True)
    if not pregenerator:
        pywikibot.bot.suggest_help(missing_generator=True)
        return False

    if not supportedSite():
        pywikibot.output(u'Sorry, this site is not supported (yet).')
        return False

    pywikibot.warning(u'This is an experimental bot')
    pywikibot.warning(u'It will only work on self published work images')
    pywikibot.warning(u'This bot is still full of bugs')
    pywikibot.warning(u'Use at your own risk!')

    prefetchQueue = Queue(maxsize=50)
    uploadQueue = Queue(maxsize=200)

    imageFetcherThread = imageFetcher(pregenerator, prefetchQueue)
    userInteractionThread = userInteraction(prefetchQueue, uploadQueue)
    uploaderThread = uploader(uploadQueue)

    imageFetcherThread.daemon = False
    userInteractionThread.daemon = False
    uploaderThread.daemon = False

    if autonomous:
        pywikibot.output('Bot is running in autonomous mode. There will be no '
                         'user interaction.')
        userInteractionThread.setAutonomous()

    if not checkTemplate:
        pywikibot.output(u'No check template will be added to the uploaded '
                         u'files.')
        uploaderThread.nochecktemplate()

    # Using the listed variables one may keep track of thread start status
    # fetchDone = imageFetcherThread.start()
    # userDone = userInteractionThread.start()
    # uploadDone = uploaderThread.start()


if __name__ == "__main__":
    main()
