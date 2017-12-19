# -*- coding: utf-8 -*-
"""
Script to copy files from a local Wikimedia wiki to Wikimedia Commons.

It uses CommonsHelper to not leave any information out and CommonSense
to automatically categorise the file. After copying, a NowCommons
template is added to the local wiki's file. It uses a local exclusion
list to skip files with templates not allow on Wikimedia Commons. If no
categories have been found, the file will be tagged on Commons.

This bot uses a graphical interface and may not work from commandline
only environment.

Requests for improvement for CommonsHelper output should be directed to
Magnus Manske at his talk page. Please be very specific in your request
(describe current output and expected output) and note an example file,
so he can test at: [[de:Benutzer Diskussion:Magnus Manske]]. You can
write him in German and English.

Examples

Work on a single image::

 python pwb.py imagecopy.py -page:Image:<imagename>

Work on the 100 newest images::

 python pwb.py imagecopy.py -newimages:100

Work on all images in a category:<cat>::

 python pwb.py imagecopy.py -cat:<cat>

Work on all images which transclude a template::

 python pwb.py imagecopy.py -transcludes:<template>

Work on a single image and deletes the image when the transfer is complete
(only works if the user has sysops privilege, otherwise it will be marked for
deletion)::

 python pwb.py imagecopy.py -page:Image:<imagename> -delete

See pagegenerators.py for more ways to get a list of images.
By default the bot works on your home wiki (set in user-config)

"""
# Based on upload.py by:
# (C) Rob W.W. Hooft, Andre Engels 2003-2007
# (C) Wikipedian, Keichwa, Leogregianin, Rikwade, Misza13 2003-2007
#
# New bot by:
# (C) Kyle/Orgullomoore, Siebrand Mazeland 2007-2008
#
# Another rewrite by:
# (C) Multichill 2008-2011
# (C) Pywikibot team, 2007-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import codecs
import re
import socket
import threading
import webbrowser

import pywikibot

from pywikibot import pagegenerators, config, i18n

from pywikibot.specialbots import UploadRobot
from pywikibot.tools import PY2

from scripts import image

if not PY2:
    import tkinter as Tkinter

    from urllib.parse import urlencode
    from urllib.request import urlopen
else:
    import Tkinter

    from urllib import urlencode, urlopen

try:
    from pywikibot.userinterfaces.gui import Tkdialog
except ImportError as _tk_error:
    Tkdialog = object

NL = ''

nowCommonsTemplate = {
    '_default': u'{{NowCommons|%s}}',
    'af': u'{{NowCommons|File:%s}}',
    'als': u'{{NowCommons|%s}}',
    'am': u'{{NowCommons|File:%s}}',
    'ang': u'{{NowCommons|File:%s}}',
    'ar': u'{{الآن كومنز|%s}}',
    'ast': u'{{EnCommons|File:%s}}',
    'az': u'{{NowCommons|%s}}',
    'bar': u'{{NowCommons|%s}}',
    'bg': u'{{NowCommons|%s}}',
    'bn': u'{{NowCommons|File:%s}}',
    'bs': u'{{NowCommons|%s}}',
    'ca': u'{{AraCommons|%s}}',
    'cs': u'{{NowCommons|%s}}',
    'cy': u'{{NowCommons|File:%s}}',
    'da': u'{{NowCommons|File:%s}}',
    'de': u'{{NowCommons|%s}}',
    'dsb': u'{{NowCommons|%s}}',
    'el': u'{{NowCommons|%s}}',
    'en': u'{{subst:ncd|%s}}',
    'eo': u'{{Nun en komunejo|%s}}',
    'es': u'{{EnCommons|File:%s}}',
    'et': u'{{NüüdCommonsis|File:%s}}',
    'fa': u'{{NowCommons|%s}}',
    'fi': u'{{NowCommons|%s}}',
    'fo': u'{{NowCommons|File:%s}}',
    'fr': u'{{Image sur Commons|%s}}',
    'fy': u'{{NowCommons|%s}}',
    'ga': u'{{Ag Cómhaoin|File:%s}}',
    'gl': u'{{EnCommons]|File:%s}}',
    'gv': u'{{NowCommons|File:%s}}',
    'he': u'{{גם בוויקישיתוף|%s}}',
    'hr': u'{{NowCommons|%s}}',
    'hsb': u'{{NowCommons|%s}}',
    'hu': u'{{Azonnali-commons|%s}}',
    'ia': u'{{NowCommons|File:%s}}',
    'id': u'{{NowCommons|File:%s}}',
    'ilo': u'{{NowCommons|File:%s}}',
    'io': u'{{NowCommons|%s}}',
    'is': u'{{NowCommons|%s}}',
    'it': u'{{NowCommons|%s}}',
    'ja': u'{{NowCommons|File:%s}}',
    'jv': u'{{NowCommons|File:%s}}',
    'ka': u'{{NowCommons|File:%s}}',
    'kn': u'{{NowCommons|File:%s}}',
    'ko': u'{{NowCommons|File:%s}}',
    'ku': u'{{NowCommons|%s}}',
    'lb': u'{{Elo op Commons|%s}}',
    'li': u'{{NowCommons|%s}}',
    'lt': u'{{NowCommons|File:%s}}',
    'lv': u'{{NowCommons|File:%s}}',
    'mk': u'{{NowCommons|File:%s}}',
    'mn': u'{{NowCommons|File:%s}}',
    'ms': u'{{NowCommons|%s}}',
    'nds-nl': u'{{NoenCommons|File:%s}}',
    'nl': u'{{NuCommons|%s}}',
    'nn': u'{{No på Commons|File:%s}}',
    'no': u'{{NowCommons|%s}}',
    'oc': u'{{NowCommons|File:%s}}',
    'pl': u'{{NowCommons|%s}}',
    'pt': u'{{NowCommons|%s}}',
    'ro': u'{{AcumCommons|File:%s}}',
    'ru': u'{{Перенесено на Викисклад|%s}}',
    'sa': u'{{NowCommons|File:%s}}',
    'scn': u'{{NowCommons|File:%s}}',
    'sh': u'{{NowCommons|File:%s}}',
    'sk': u'{{NowCommons|File:%s}}',
    'sl': u'{{OdslejZbirka|%s}}',
    'sq': u'{{NowCommons|File:%s}}',
    'sr': u'{{NowCommons|File:%s}}',
    'st': u'{{NowCommons|File:%s}}',
    'su': u'{{IlaharKiwari|File:%s}}',
    'sv': u'{{NowCommons|%s}}',
    'sw': u'{{NowCommons|%s}}',
    'ta': u'{{NowCommons|File:%s}}',
    'th': u'{{มีที่คอมมอนส์|File:%s}}',
    'tl': u'{{NasaCommons|File:%s}}',
    'tr': u'{{NowCommons|%s}}',
    'uk': u'{{NowCommons|File:%s}}',
    'ur': u'{{NowCommons|File:%s}}',
    'vec': u'{{NowCommons|%s}}',
    'vi': u'{{NowCommons|File:%s}}',
    'vo': u'{{InKobädikos|%s}}',
    'wa': u'{{NowCommons|%s}}',
    'zh': u'{{NowCommons|File:%s}}',
    'zh-min-nan': u'{{Commons ū|%s}}',
    'zh-yue': u'{{subst:Ncd|File:%s}}',
}

moveToCommonsTemplate = {
    'ar': [u'نقل إلى كومنز'],
    'en': [u'Commons ok', u'Copy to Wikimedia Commons', u'Move to commons',
           u'Movetocommons', u'To commons',
           u'Copy to Wikimedia Commons by BotMultichill'],
    'fi': [u'Commonsiin'],
    'fr': [u'Image pour Commons'],
    'hsb': [u'Kopěruj do Wikimedia Commons'],
    'hu': [u'Commonsba'],
    'is': [u'Færa á Commons'],
    'ms': [u'Hantar ke Wikimedia Commons'],
    'nl': [u'Verplaats naar Wikimedia Commons', u'VNC'],
    'pl': [u'Do Commons', u'NaCommons', u'Na Commons'],
    'ru': [u'На Викисклад'],
    'sl': [u'Skopiraj v Zbirko'],
    'sr': [u'За оставу'],
    'sv': [u'Till Commons'],
    'zh': [u'Copy to Wikimedia Commons'],
}


def pageTextPost(url, parameters):
    """Get data from commons helper page."""
    gotInfo = False
    while not gotInfo:
        try:
            commonsHelperPage = urlopen(
                "http://tools.wmflabs.org/commonshelper/index.php", parameters)
            data = commonsHelperPage.read().decode('utf-8')
            gotInfo = True
        except IOError:
            pywikibot.output(u'Got an IOError, let\'s try again')
        except socket.timeout:
            pywikibot.output(u'Got a timeout, let\'s try again')
    return data


class imageTransfer(threading.Thread):

    """Facilitate transfer of image/file to commons."""

    def __init__(self, imagePage, newname, category, delete_after_done=False):
        """Constructor."""
        self.imagePage = imagePage
        self.newname = newname
        self.category = category
        self.delete_after_done = delete_after_done
        threading.Thread.__init__(self)

    def run(self):
        """Run the bot."""
        tosend = {'language': self.imagePage.site.lang.encode('utf-8'),
                  'image': self.imagePage.title(
                      withNamespace=False).encode('utf-8'),
                  'newname': self.newname.encode('utf-8'),
                  'project': self.imagePage.site.family.name.encode('utf-8'),
                  'username': '',
                  'commonsense': '1',
                  'remove_categories': '1',
                  'ignorewarnings': '1',
                  'doit': 'Uitvoeren'
                  }

        tosend = urlencode(tosend)
        pywikibot.output(tosend)
        CH = pageTextPost('http://tools.wmflabs.org/commonshelper/index.php',
                          tosend)
        pywikibot.output('Got CH desc.')

        tablock = CH.split('<textarea ')[1].split('>')[0]
        CH = CH.split('<textarea ' + tablock + '>')[1].split('</textarea>')[0]
        CH = CH.replace(u'&times;', u'×')
        CH = self.fixAuthor(CH)
        pywikibot.output(CH)

        # I want every picture to be tagged with the bottemplate so i can check
        # my contributions later.
        CH = ('\n\n{{BotMoveToCommons|' + self.imagePage.site.lang +
              '.' + self.imagePage.site.family.name +
              '|year={{subst:CURRENTYEAR}}|month={{subst:CURRENTMONTHNAME}}'
              '|day={{subst:CURRENTDAY}}}}' + CH)

        if self.category:
            CH = CH.replace('{{subst:Unc}} <!-- Remove this line once you have '
                            'added categories -->', '')
            CH += u'[[Category:' + self.category + u']]'

        bot = UploadRobot(url=self.imagePage.fileUrl(), description=CH,
                          useFilename=self.newname, keepFilename=True,
                          verifyDescription=False, ignoreWarning=True,
                          targetSite=pywikibot.Site('commons', 'commons'))
        bot.run()

        # Should check if the image actually was uploaded
        if pywikibot.Page(pywikibot.Site('commons', 'commons'),
                          u'Image:' + self.newname).exists():
            # Get a fresh copy, force to get the page so we dont run into edit
            # conflicts
            imtxt = self.imagePage.get(force=True)

            # Remove the move to commons templates
            if self.imagePage.site.lang in moveToCommonsTemplate:
                for moveTemplate in moveToCommonsTemplate[
                        self.imagePage.site.lang]:
                    imtxt = re.sub(r'(?i)\{\{' + moveTemplate + r'[^\}]*\}\}',
                                   '', imtxt)

            # add {{NowCommons}}
            if self.imagePage.site.lang in nowCommonsTemplate:
                addTemplate = nowCommonsTemplate[
                    self.imagePage.site.lang] % self.newname
            else:
                addTemplate = nowCommonsTemplate['_default'] % self.newname

            commentText = i18n.twtranslate(
                self.imagePage.site,
                'commons-file-now-available',
                {'localfile': self.imagePage.title(withNamespace=False),
                 'commonsfile': self.newname})

            pywikibot.showDiff(self.imagePage.get(), imtxt + addTemplate)
            self.imagePage.put(imtxt + addTemplate, comment=commentText)

            self.gen = pagegenerators.FileLinksGenerator(self.imagePage)
            self.preloadingGen = pagegenerators.PreloadingGenerator(self.gen)

            moveSummary = i18n.twtranslate(
                self.imagePage.site,
                'commons-file-moved',
                {'localfile': self.imagePage.title(withNamespace=False),
                 'commonsfile': self.newname})

            # If the image is uploaded under a different name, replace all
            # instances
            if self.imagePage.title(withNamespace=False) != self.newname:
                imagebot = image.ImageRobot(
                    generator=self.preloadingGen,
                    oldImage=self.imagePage.title(withNamespace=False),
                    newImage=self.newname,
                    summary=moveSummary, always=True, loose=True)
                imagebot.run()

            # If the user want to delete the page and
            # the user has sysops privilege, delete the page, otherwise
            # it will be marked for deletion.
            if self.delete_after_done:
                self.imagePage.delete(moveSummary, False)
        return

    def fixAuthor(self, pageText):
        """Fix the author field in the information template."""
        informationRegex = re.compile(
            r'\|Author=Original uploader was '
            r'(?P<author>\[\[:\w+:\w+:\w+\|\w+\]\] at \[.+\])')
        selfRegex = re.compile(
            r'{{self\|author='
            r'(?P<author>\[\[:\w+:\w+:\w+\|\w+\]\] at \[.+\])\|')

        # Find the |Author=Original uploader was ....
        informationMatch = informationRegex.search(pageText)

        # Find the {{self|author=
        selfMatch = selfRegex.search(pageText)

        # Check if both are found and are equal
        if (informationMatch and selfMatch):
            if informationMatch.group('author') == selfMatch.group('author'):
                # Replace |Author=Original uploader was ... with |Author= ...
                pageText = informationRegex.sub(r'|Author=\g<author>',
                                                pageText)
        return pageText


# -label ok skip view
# textarea
archivo = config.datafilepath("Uploadbot.localskips.txt")
try:
    open(archivo, 'r')
except IOError:
    tocreate = open(archivo, 'w')
    tocreate.write("{{NowCommons")
    tocreate.close()


def getautoskip():
    """Get a list of templates to skip."""
    f = codecs.open(archivo, 'r', 'utf-8')
    txt = f.read()
    f.close()
    toreturn = txt.split('{{')[1:]
    return toreturn


class TkdialogIC(Tkdialog):

    """The dialog window for image info."""

    def __init__(self, image_title, content, uploader, url, templates,
                 commonsconflict=0):
        """Constructor."""
        super(TkdialogIC, self).__init__()
        self.root = Tkinter.Tk()
        # "%dx%d%+d%+d" % (width, height, xoffset, yoffset)
        # Always appear the same size and in the bottom-left corner
        self.root.geometry("600x200+100-100")
        self.root.title(image_title)
        self.changename = ''
        self.skip = 0
        self.url = url
        self.uploader = "Unknown"
        # uploader.decode('utf-8')
        scrollbar = Tkinter.Scrollbar(self.root, orient=Tkinter.VERTICAL)
        label = Tkinter.Label(self.root, text='Enter new name or leave blank.')
        imageinfo = Tkinter.Label(self.root, text='Uploaded by %s.' % uploader)
        textarea = Tkinter.Text(self.root)
        textarea.insert(Tkinter.END, content.encode('utf-8'))
        textarea.config(state=Tkinter.DISABLED,
                        height=8, width=40, padx=0, pady=0,
                        wrap=Tkinter.WORD, yscrollcommand=scrollbar.set)
        scrollbar.config(command=textarea.yview)
        self.entry = Tkinter.Entry(self.root)

        self.templatelist = Tkinter.Listbox(self.root, bg="white", height=5)

        for template in templates:
            self.templatelist.insert(Tkinter.END, template)
        autoskip_button = Tkinter.Button(self.root, text="Add to AutoSkip",
                                         command=self.add2_auto_skip)
        browser_button = Tkinter.Button(self.root, text='View in browser',
                                        command=self.open_in_browser)
        skip_button = Tkinter.Button(self.root, text='Skip',
                                     command=self.skip_file)
        ok_button = Tkinter.Button(self.root, text="OK", command=self.ok_file)

        # Start grid
        label.grid(row=0)
        ok_button.grid(row=0, column=1, rowspan=2)
        skip_button.grid(row=0, column=2, rowspan=2)
        browser_button.grid(row=0, column=3, rowspan=2)

        self.entry.grid(row=1)

        textarea.grid(row=2, column=1, columnspan=3)
        scrollbar.grid(row=2, column=5)
        self.templatelist.grid(row=2, column=0)

        autoskip_button.grid(row=3, column=0)
        imageinfo.grid(row=3, column=1, columnspan=4)

    def ok_file(self):
        """The user pressed the OK button."""
        self.changename = self.entry.get()
        self.root.destroy()

    def getnewname(self):
        """
        Activate dialog.

        @return: new name and if the image is skipped
        @rtype: tuple
        """
        self.root.mainloop()
        return (self.changename, self.skip)

    def open_in_browser(self):
        """The user pressed the View in browser button."""
        webbrowser.open(self.url)

    def add2_auto_skip(self):
        """The user pressed the Add to AutoSkip button."""
        templateid = int(self.templatelist.curselection()[0])
        template = self.templatelist.get(templateid)
        with codecs.open(archivo, 'a', 'utf-8') as f:
            f.write('{{' + template)
        self.skip_file()


def doiskip(pagetext):
    """Skip this image or not.

    Returns True if the image is on the skip list, otherwise False
    """
    saltos = getautoskip()
    # print saltos
    for salto in saltos:
        rex = r'\{\{\s*[' + salto[0].upper() + salto[0].lower() + r']' + \
              salto[1:] + r'(\}\}|\|)'
        # print rex
        if re.search(rex, pagetext):
            return True
    return False


def main(*args):
    """Process command line arguments and invoke bot."""
    imagepage = None
    always = False
    category = u''
    delete_after_done = False
    # Load a lot of default generators
    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        if arg == '-always':
            always = True
        elif arg.startswith('-cc:'):
            category = arg[len('-cc:'):]
        elif arg == '-delete':
            delete_after_done = True
        else:
            genFactory.handleArg(arg)

    pregenerator = genFactory.getCombinedGenerator(preload=True)
    if not pregenerator:
        pywikibot.bot.suggest_help(missing_generator=True)
        return False

    for page in pregenerator:
        skip = False
        if page.exists() and (page.namespace() == 6) and (
                not page.isRedirectPage()):
            imagepage = pywikibot.FilePage(page.site, page.title())

            # First do autoskip.
            if doiskip(imagepage.get()):
                pywikibot.output("Skipping " + page.title())
                skip = True
            else:
                # The first upload is last in the list.
                try:
                    username = imagepage.getLatestUploader()[0]
                except NotImplementedError:
                    # No API, using the page file instead
                    (datetime, username, resolution, size,
                     comment) = imagepage.getFileVersionHistory().pop()
                if always:
                    newname = imagepage.title(withNamespace=False)
                    CommonsPage = pywikibot.Page(pywikibot.Site('commons',
                                                                'commons'),
                                                 u'File:%s' % newname)
                    if CommonsPage.exists():
                        skip = True
                else:
                    while True:
                        # Do the TkdialogIC to accept/reject and change te name
                        (newname, skip) = TkdialogIC(
                            imagepage.title(withNamespace=False),
                            imagepage.get(), username,
                            imagepage.permalink(with_protocol=True),
                            imagepage.templates()).getnewname()

                        if skip:
                            pywikibot.output('Skipping this image')
                            break

                        # Did we enter a new name?
                        if len(newname) == 0:
                            # Take the old name
                            newname = imagepage.title(withNamespace=False)
                        else:
                            newname = newname.decode('utf-8')

                        # Check if the image already exists
                        CommonsPage = pywikibot.Page(
                            pywikibot.Site('commons', 'commons'),
                            u'File:' + newname)
                        if not CommonsPage.exists():
                            break
                        else:
                            pywikibot.output(
                                'Image already exists, pick another name or '
                                'skip this image')
                        # We dont overwrite images, pick another name, go to
                        # the start of the loop

            if not skip:
                imageTransfer(imagepage, newname, category,
                              delete_after_done).start()

    pywikibot.output('Still ' + str(threading.activeCount()) +
                     ' active threads, lets wait')
    for openthread in threading.enumerate():
        if openthread != threading.currentThread():
            openthread.join()
    pywikibot.output(u'All threads are done')


if __name__ == "__main__":
    main()
