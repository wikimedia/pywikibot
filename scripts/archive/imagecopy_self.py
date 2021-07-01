"""
Script to copy self published files from English Wikipedia to Commons.

This bot is based on imagecopy.py and intended to be used to empty out
https://en.wikipedia.org/wiki/Category:Self-published_work

This bot uses a graphical interface and may not work from commandline
only environment.

Examples
--------

Work on a single file:

    python pwb.py imagecopy -page:file:<filename>

Work on all images in a category:<cat>:

    python pwb.py imagecopy -cat:<cat>

Work on all images which transclude a template:

    python pwb.py imagecopy -transcludes:<template>

See pagegenerators.py for more ways to get a list of images.
By default the bot works on your home wiki (set in user-config)

This is a first test version and should be used with care.

Use -nochecktemplate if you don't want to add the check template. Be sure to
check it yourself.
"""
#
# (C) Pywikibot team, 2003-2020
#
# Distributed under the terms of the MIT license.
#
import re
import threading
import webbrowser
from datetime import datetime
from queue import Queue
from textwrap import fill

import pywikibot
from pywikibot import i18n, pagegenerators
from pywikibot.specialbots import UploadRobot
from pywikibot.textlib import removeCategoryLinks
from scripts import image, imagerecat


try:
    from pywikibot.userinterfaces.gui import Tkdialog, Tkinter
except ImportError as _tk_error:
    Tkinter = _tk_error
    Tkdialog = object

NL = ''

CID_INFO = """\
{{{{Information
|description={description}
|date={date}
|source={source}
|author={author}
|permission={permission}
|other_versions={other_versions}
}}}}
"""

nowCommonsTemplate = {
    'ar': '{{الآن كومنز|%s}}',
    'ary': '{{Now Commons|%s}}',
    'arz': '{{Now Commons|%s}}',
    'de': '{{NowCommons|%s}}',
    'en': ('{{NowCommons|1=File:%s|date=~~~~~|'
           'reviewer={{subst:REVISIONUSER}}}}'),
    'lb': '{{Elo op Commons|%s}}',
    'nds-nl': '{{NoenCommons|1=File:%s}}',
    'shared': ('{{NowCommons|1=File:%s|date=~~~~~|'
               'reviewer={{subst:REVISIONUSER}}}}'),
}

moveToCommonsTemplate = {
    'ar': ['نقل إلى كومنز', 'Copy to Wikimedia Commons'],
    'ary': ['نقل إلى كومنز', 'Copy to Wikimedia Commons'],
    'arz': ['نقل ل كومنز', 'Copy to Wikimedia Commons'],
    'de': ['NowCommons', 'NC', 'NCT', 'Nowcommons'],
    'en': ['Commons ok', 'Copy to Wikimedia Commons', 'Move to commons',
           'Movetocommons', 'To commons',
           'Copy to Wikimedia Commons by BotMultichill'],
    'lb': ['Move to commons'],
    'nds-nl': ['Noar Commons', 'VNC'],
    'shared': ['Move'],
}

skipTemplates = {
    'ar': ['NowCommons',
           'الآن كومونز',
           ],
    'ary': ['NowCommons', ],
    'arz': ['NowCommons', ],
    'de': ['Löschprüfung',
           'NoCommons',
           'NowCommons',
           'NowCommons/Mängel',
           'NowCommons-Überprüft',
           'Wappenrecht',
           ],
    'en': ['Db-f1',
           'Db-f2',
           'Db-f3',
           'Db-f7',
           'Db-f8',
           'Db-f9',
           'Db-f10',
           'Do not move to Commons',
           'NowCommons',
           'CommonsNow',
           'Nowcommons',
           'NowCommonsThis',
           'Nowcommons2',
           'NCT',
           'Nowcommonsthis',
           'Moved to commons',
           'Now Commons',
           'Now at commons',
           'Db-nowcommons',
           'WikimediaCommons',
           'Now commons',
           'Di-no source',
           'Di-no license',
           'Di-no permission',
           'Di-orphaned fair use',
           'Di-no source no license',
           'Di-replaceable fair use',
           'Di-no fair use rationale',
           'Di-disputed fair use rationale',
           'Puf',
           'PUI',
           'Pui',
           'Ffd',
           'PD-user',  # Only the self templates are supported for now.
           'Ticket Scan',
           'Non-free 2D art',
           'Non-free 3D art',
           'Non-free architectural work',
           'Non-free fair use in',
           ],
    'lb': ['Läschen',
           ],
    'nds-nl': ['Allinnig Wikipedie',
               'Bepark',
               'Gienidee',
               'NoenCommons',
               'NowCommons',
               ],
    'shared': [''],
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
    'ar': 'معلومات',
    'ary': 'معلومات',
    'arz': 'معلومات',
    'de': 'Information',
    'en': 'Information',
    'lb': 'Information',
    'nds-nl': 'Information',
    'shared': 'Information',
}

informationFields = {
    'ar': {
        'location': 'remarks',
        'وصف': 'description',
        'مصدر': 'source',
        'تاريخ': 'date',
        'منتج': 'author',
        'إذن': 'permission',
        'نسخ أخرى': 'other versions',
    },
    'ary': {
        'location': 'remarks',
        'وصف': 'description',
        'مصدر': 'source',
        'تاريخ': 'date',
        'منتج': 'author',
        'إذن': 'permission',
        'نسخ أخرى': 'other versions',
    },
    'arz': {
        'location': 'remarks',
        'وصف': 'description',
        'مصدر': 'source',
        'تاريخ': 'date',
        'منتج': 'author',
        'إذن': 'permission',
        'نسخ أخرى': 'other versions',
    },
    'de': {
        'anmerkungen': 'remarks',  # FIXME: More flexible
        'beschreibung': 'description',
        'quelle': 'source',
        'datum': 'date',
        'urheber': 'author',
        'permission': 'permission',
        'andere Versione': 'other versions',
    },
    'en': {
        'location': 'remarks',
        'description': 'description',
        'source': 'source',
        'date': 'date',
        'author': 'author',
        'permission': 'permission',
        'other versions': 'other versions',
    },
    'lb': {
        'location': 'remarks',
        'description': 'description',
        'source': 'source',
        'date': 'date',
        'author': 'author',
        'permission': 'permission',
        'other versions': 'other versions',
    },
    'nds-nl': {
        'location': 'remarks',
        'description': 'description',
        'source': 'source',
        'date': 'date',
        'author': 'author',
        'permission': 'permission',
        'other versions': 'other versions',
    },
    'shared': {
        'description': 'description',
        'source': 'source',
        'date': 'date',
        'author': 'author',
        'permission': 'permission',
        'other versions': 'other versions',
    },
}


def supportedSite():
    """Check if this site is supported."""
    site = pywikibot.Site()
    l10n_dicts = [
        nowCommonsTemplate,
        moveToCommonsTemplate,
        skipTemplates,
        licenseTemplates,
        sourceGarbage,
        informationTemplate,
        informationFields,
    ]
    return all(site.code in elem for elem in l10n_dicts)


class imageFetcher(threading.Thread):

    """Tries to fetch information for all images in the generator."""

    def __init__(self, pagegenerator, prefetchQueue):
        """Initializer."""
        self.pagegenerator = pagegenerator
        self.prefetchQueue = prefetchQueue
        imagerecat.initLists()
        super().__init__()

    def run(self):
        """Run imageFetcher."""
        for page in self.pagegenerator:
            self.processImage(page)
        self.prefetchQueue.put(None)
        pywikibot.output('Fetched all images.')
        return True

    def processImage(self, page):
        """Work on a single image."""
        if not page.exists() or page.namespace() != 6 or page.isRedirectPage():
            return

        imagepage = pywikibot.FilePage(page.site(), page.title())

        # First do autoskip.
        if self.doiskip(imagepage):
            pywikibot.output(
                'Skipping {} : Got a template on the skip list.'
                .format(page.title()))
            return

        text = imagepage.get()
        for regex, _ in licenseTemplates[page.site.lang]:
            match = re.search(regex, text, flags=re.IGNORECASE)
            if match:
                break
        else:
            pywikibot.output(
                'Skipping {} : No suitable license template was found.'
                .format(page.title()))
            return

        self.prefetchQueue.put(self.getNewFields(imagepage))

    def doiskip(self, imagepage):
        """Skip this image or not.

        Returns True if the image is on the skip list, otherwise False

        """
        for template in imagepage.templates():
            template_title = template.title(with_ns=False)
            if template_title in skipTemplates[imagepage.site.lang]:
                pywikibot.output(
                    'Found {} which is on the template skip list'
                    .format(template_title))
                return True
        return False

    def getNewFields(self, imagepage):
        """Build a new description based on the imagepage."""
        if '{{Information' in imagepage.get() \
           or '{{information' in imagepage.get():
            (description, date, source, author, permission,
             other_versions) = self.getNewFieldsFromInformation(imagepage)
        else:
            (description, date, source,
             author) = self.getNewFieldsFromFreetext(imagepage)
            permission = ''
            other_versions = ''

        licensetemplate = self.getNewLicensetemplate(imagepage)
        categories = self.getNewCategories(imagepage)
        return {'imagepage': imagepage,
                'filename': imagepage.title(with_ns=False),
                'description': description,
                'date': date,
                'source': source,
                'author': author,
                'permission': permission,
                'other_versions': other_versions,
                'licensetemplate': licensetemplate,
                'categories': categories,
                'skip': False}

    def getNewFieldsFromInformation(self, imagepage):
        """Extract fields from current information template for new template.

        :param imagepage: The file page to get the template.
        :type imagepage: pywikibot.FilePage
        """
        # fields = ['location', 'description', 'source', 'date', 'author',
        #           'permission', 'other versions']
        # FIXME: The implementation for German has to be checked for the
        #        "strange" fields

        description = ''
        permission = ''
        other_versions = ''
        contents = {
            value: ''
            for value in informationFields[imagepage.site.lang].values()
        }

        information = informationTemplate[imagepage.site.lang]
        fields = informationFields[imagepage.site.lang]

        for template, params in imagepage.templatesWithParams():
            if template.title() == information:
                for param in params:
                    # Split at =
                    field, _, value = param.partition('=')
                    # To lowercase, remove underscores and strip spaces
                    field = field.lower().replace('_', ' ').strip()
                    key = fields.get(field)
                    # See if first part is in fields list
                    if key:
                        # Ok, field is good, store it.
                        contents[key] = value.strip()

        # We now got the contents from the old information template.
        # Let's get the info for the new one

        # Description
        # FIXME: Add {{<lang>|<original text>}} if <lang is valid at Commons
        if contents['description']:
            description = self.convertLinks(contents['description'],
                                            imagepage.site())
        if 'remarks' in contents:
            if description == '':
                description = self.convertLinks(contents['remarks'],
                                                imagepage.site())
            else:
                description += '<BR/>\n' + self.convertLinks(
                    contents['remarks'], imagepage.site())

        # Source
        source = self.getSource(imagepage,
                                source=self.convertLinks(contents['source'],
                                                         imagepage.site()))

        # Date
        date = contents['date'] or self.getUploadDate(imagepage)

        # Author
        if contents['author'] \
           and contents['author'] != self.getAuthor(imagepage):
            author = self.convertLinks(contents['author'], imagepage.site())
        else:
            author = self.getAuthorText(imagepage)

        # Permission
        # Still have to filter out crap like "see below" or "yes"
        if contents['permission']:
            # Strip of the license template if it's in the permission section
            for regex, _ in licenseTemplates[imagepage.site.lang]:
                contents['permission'] = re.sub(regex, '',
                                                contents['permission'],
                                                flags=re.IGNORECASE)
            permission = self.convertLinks(contents['permission'],
                                           imagepage.site())

        # Other_versions
        if contents['other versions']:
            other_versions = self.convertLinks(contents['other versions'],
                                               imagepage.site())

        return (description, date, source, author, permission, other_versions)

    def getNewFieldsFromFreetext(self, imagepage):
        """Extract fields from free text for the new information template."""
        text = imagepage.get()

        for toRemove in sourceGarbage[imagepage.site.lang]:
            text = re.sub(toRemove, '', text, flags=re.IGNORECASE)

        for regex, _ in licenseTemplates[imagepage.site.lang]:
            text = re.sub(regex, '', text, flags=re.IGNORECASE)

        text = removeCategoryLinks(text, imagepage.site())

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
        uploadtime = imagepage.get_file_history()[-1][0]
        uploadDatetime = datetime.strptime(uploadtime, '%Y-%m-%dT%H:%M:%SZ')
        return ('{{Date|%s|%s|%s}} (original upload date)'
                % (uploadDatetime.year,
                   uploadDatetime.month,
                   uploadDatetime.day))

    def getSource(self, imagepage, source=''):
        """Get text to put in the source field of new information template."""
        site = imagepage.site()
        lang = site.code
        family = site.family.name
        if not source:
            source = '{{Own}}'

        return (source.strip()
                + '<BR />Transferred from [http://{lang}.{family}.org '
                '{lang}.{family}]').format(lang=lang, family=family)

    def getAuthorText(self, imagepage):
        """Get uploader to put in the author field of information template."""
        site = imagepage.site()
        lang = site.code
        family = site.family.name

        firstuploader = self.getAuthor(imagepage)
        return '[[:{lang}:User:{firstuploader}|{firstuploader}]] at ' \
               '[http://{lang}.{family}.org {lang}.{family}]'.format(
                   lang=lang, family=family, firstuploader=firstuploader)

    def getAuthor(self, imagepage):
        """Get the first uploader."""
        return imagepage.get_file_history()[-1][1].strip()

    def convertLinks(self, text, sourceSite):
        """Convert links from the current wiki to Commons."""
        lang = sourceSite.code
        family = sourceSite.family.name
        conversions = [
            (r'\[\[([^\[\]\|]+)\|([^\[\]\|]+)\]\]', r'[[:{lang}:\1|\2]]'),
            (r'\[\[([^\[\]\|]+)\]\]', r'[[:{lang}:\1|\1]]'),
        ]
        for (regex, replacement) in conversions:
            text = re.sub(regex, replacement.format(lang=lang,
                                                    family=family), text)
        return text

    def getNewLicensetemplate(self, imagepage):
        """Get a license template to put on the image to be uploaded."""
        text = imagepage.get()
        site = imagepage.site()
        lang = site.code
        family = site.family.name
        result = ''
        for (regex,
             replacement) in licenseTemplates[imagepage.site.lang]:
            match = re.search(regex, text, flags=re.IGNORECASE)
            if match:
                result = re.sub(regex, replacement, match.group(0),
                                flags=re.IGNORECASE)
                return result % {'author': self.getAuthor(imagepage),
                                 'lang': lang,
                                 'family': family}
        return result

    def getNewCategories(self, imagepage):
        """Get categories for the image.

        Don't forget to filter.
        """
        result = ''
        (commonshelperCats, usage,
         galleries) = imagerecat.getCommonshelperCats(imagepage)
        newcats = imagerecat.applyAllFilters(commonshelperCats)
        for newcat in newcats:
            result += '[[Category:{}]] '.format(newcat)
        return result


class userInteraction(threading.Thread):

    """Prompt all images to the user."""

    def __init__(self, prefetchQueue, uploadQueue):
        """Initializer."""
        self.prefetchQueue = prefetchQueue
        self.uploadQueue = uploadQueue
        self.autonomous = False
        super().__init__()

    def run(self):
        """Run thread."""
        while True:
            fields = self.prefetchQueue.get()
            if not fields:
                break
            self.processImage(fields)

        self.uploadQueue.put(None)
        pywikibot.output('User worked on all images.')
        return True

    def setAutonomous(self):
        """Don't do any user interaction."""
        self.autonomous = True

    def processImage(self, fields):
        """Work on a single image."""
        if self.autonomous:
            # Check if the image already exists. Do nothing if the name is
            # already taken.
            CommonsPage = pywikibot.Page(pywikibot.Site('commons',
                                                        'commons'),
                                         'File:' + fields.get('filename'))
            if CommonsPage.exists():
                return
        else:
            while True:
                # Do the TkdialogICS to accept/reject and change the name
                fields = TkdialogICS(fields).getnewmetadata()

                if fields.get('skip'):
                    pywikibot.output('Skipping {} : User pressed skip.'
                                     .format(fields.get('imagepage').title()))
                    return

                # Check if the image already exists
                CommonsPage = pywikibot.Page(pywikibot.Site('commons',
                                                            'commons'),
                                             'File:' + fields.get('filename'))
                if not CommonsPage.exists():
                    break

                # We don't overwrite images, pick another name, go to the
                # start of the loop
                pywikibot.output('Image already exists, pick another name '
                                 'or skip this image')

        # Put the fields in the queue to be uploaded
        self.uploadQueue.put(fields)


class TkdialogICS(Tkdialog):

    """The dialog window for image info."""

    fieldnames = ['author', 'categories', 'date', 'description', 'filename',
                  'imagepage', 'licensetemplate', 'other_versions',
                  'permission', 'source']

    def __init__(self, fields):
        """Initializer.

        fields:
            imagepage, description, date, source, author, licensetemplate,
            categories
        """
        # Check if `Tkinter` wasn't imported
        if isinstance(Tkinter, ImportError):
            raise Tkinter

        self.root = Tkinter.Tk()
        # "%dx%d%+d%+d" % (width, height, xoffset, yoffset)
        # Always appear the same size and in the bottom-left corner
        # FIXME : Base this on the screen size or make it possible for the user
        # to configure this

        # Get all the relevant fields
        super().__init__()
        for name in self.fieldnames:
            setattr(self, name, fields.get(name))

        self.skip = False

        # Start building the page
        self.root.geometry('1500x400+100-100')
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
        self.filename_label = Tkinter.Label(self.root, text='Filename : ')
        self.information_description_label = Tkinter.Label(
            self.root, text='Description : ')
        self.information_date_label = Tkinter.Label(self.root, text='Date : ')
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
            self.root, text='Categories : ')

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

        return {name: getattr(self, name)
                for name in self.fieldnames + ['skip']}

    def open_in_browser(self):
        """The user pressed the View in browser button."""
        webbrowser.open(self.url)


class uploader(threading.Thread):

    """Upload all images."""

    def __init__(self, uploadQueue):
        """Initializer."""
        self.uploadQueue = uploadQueue
        self.checktemplate = True
        super().__init__()

    def run(self):
        """Run uploader."""
        while True:  # Change later
            fields = self.uploadQueue.get()
            if not fields:
                break
            self.processImage(fields)
        return True

    def nochecktemplate(self):
        """Don't want to add {{BotMoveToCommons}}."""
        self.checktemplate = False

    def processImage(self, fields):
        """Work on a single image."""
        cid = self.buildNewImageDescription(fields)
        pywikibot.output(cid)
        bot = UploadRobot(url=fields.get('imagepage').get_file_url(),
                          description=cid,
                          use_filename=fields.get('filename'),
                          keep_filename=True, verify_description=False,
                          ignore_warning=True,
                          target_site=pywikibot.Site('commons', 'commons'))
        bot.run()

        imagepage = fields.get('imagepage')
        filename = fields.get('filename')
        self.tagNowcommons(imagepage, filename)
        self.replaceUsage(imagepage, filename)

    def buildNewImageDescription(self, fields):
        """Build a new information template."""
        site = fields.get('imagepage').site()
        lang = site.code
        family = site.family.name

        cid = ''
        if self.checktemplate:
            cid += ('\n{{BotMoveToCommons|%(lang)s.%(family)s'
                    '|year={{subst:CURRENTYEAR}}'
                    '|month={{subst:CURRENTMONTHNAME}}'
                    '|day={{subst:CURRENTDAY}}}}\n'
                    % {'lang': lang, 'family': family}
        cid += '== {{int:filedesc}} ==\n'
        cid += CID_INFO.format_map(fields)
        cid += '== {{int:license}} ==\n'
        cid += '{licensetemplate}\n'.format_map(fields)
        cid += '\n'
        cid += self.getOriginalUploadLog(fields.get('imagepage'))
        cid += '__NOTOC__\n'
        if not fields.get('categories').strip():
            cid = cid + '{{Subst:Unc}}'
        else:
            cid = cid + '{categories}\n'.format_map(fields)
        return cid

    def getOriginalUploadLog(self, imagepage):
        """Get upload log to put at the bottom of the image description page.

        :param imagepage: The file page to retrieve the log.
        :type imagepage: pywikibot.FilePage
        """
        filehistory = imagepage.get_file_history()
        filehistory.reverse()

        site = imagepage.site()
        lang = site.code
        family = site.family.name

        sourceimage = imagepage.site.get_address(
            imagepage.title()).replace('&redirect=no&useskin=monobook', '')

        result = '== {{Original upload log}} ==\n'
        result += ('The original description page is/was '
                   '[http://{lang}.{family}.org{sourceimage} here]. '
                   'All following user names refer to {lang}.{family}.\n'
                   .format(lang=lang, family=family, sourceimage=sourceimage))
        for (timestamp, username, resolution, size, comment) in filehistory:
            date = datetime.strptime(
                timestamp, '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d %H:%M')
            result += (
                '* {date} [[:{lang}:user:{username}|{username}]] '
                "{resolution} ({size} bytes) ''"
                "<nowiki>{comment}</nowiki>''\n"
                .format(lang=lang, date=date, username=username,
                        resolution=resolution, size=size, comment=comment))

        return result

    def tagNowcommons(self, imagepage, filename):
        """Tagged the imag which has been moved to Commons for deletion."""
        if pywikibot.Page(pywikibot.Site('commons', 'commons'),
                          'File:' + filename).exists():
            # Get a fresh copy, force to get the page so we don't run into edit
            # conflicts
            imtxt = imagepage.get(force=True)

            # Remove the move to commons templates
            if imagepage.site.lang in moveToCommonsTemplate:
                for moveTemplate in moveToCommonsTemplate[
                        imagepage.site.lang]:
                    imtxt = re.sub(r'(?i){{' + moveTemplate + r'[^}]*}}',
                                   r'',
                                   imtxt)

            # add {{NowCommons}}
            if imagepage.site.lang in nowCommonsTemplate:
                addTemplate = nowCommonsTemplate[
                    imagepage.site.lang] % filename
            else:
                addTemplate = nowCommonsTemplate['_default'] % filename

            commentText = i18n.twtranslate(
                imagepage.site(), 'commons-file-now-available',
                {'localfile': imagepage.title(with_ns=False),
                 'commonsfile': filename})

            pywikibot.showDiff(imagepage.get(), imtxt + addTemplate)
            imagepage.put(imtxt + addTemplate, comment=commentText)

    def replaceUsage(self, imagepage, filename):
        """Replace all usage if image is uploaded under a different name."""
        if imagepage.title(with_ns=False) != filename:
            gen = pagegenerators.FileLinksGenerator(imagepage)
            preloadingGen = pagegenerators.PreloadingGenerator(gen)

            moveSummary = i18n.twtranslate(
                imagepage.site(), 'commons-file-moved',
                {'localfile': imagepage.title(with_ns=False),
                 'commonsfile': filename})

            imagebot = image.ImageRobot(
                generator=preloadingGen,
                oldImage=imagepage.title(with_ns=False),
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
            genFactory.handle_arg()(arg)

    pregenerator = genFactory.getCombinedGenerator(preload=True)
    additional_text = ('' if supportedSite()
                       else 'Sorry, this site is not supported (yet).')
    if pywikibot.bot.suggest_help(missing_generator=not pregenerator,
                                  additional_text=additional_text):
        return

    pywikibot.warning(fill('This is an experimental bot. '
                           'It will only work on self published work images. '
                           'This bot is still full of bugs. '
                           'Use at your own risk!'))

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
        pywikibot.output('No check template will be added to the uploaded '
                         'files.')
        uploaderThread.nochecktemplate()

    # Using the listed variables one may keep track of thread start status
    # fetchDone = imageFetcherThread.start()
    # userDone = userInteractionThread.start()
    # uploadDone = uploaderThread.start()


if __name__ == '__main__':
    main()
