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

Command line options:

-always      Skip the GUI validation

-setcat:     Set the category of the copied image

-delete      Delete the image after the image has been transferred. This will
             only work if the user has sysops privileges, otherwise the image
             will only be marked for deletion.

&params;

Examples
--------

Work on a single image:

    python pwb.py imagecopy -page:Image:<imagename>

Work on the 100 newest images:

    python pwb.py imagecopy -newimages:100

Work on all images in a category:<cat>:

    python pwb.py imagecopy -cat:<cat>

Work on all images which transclude a template:

    python pwb.py imagecopy -transcludes:<template>

Work on a single image and deletes the image when the transfer is complete
(only works if the user has sysops privilege, otherwise it will be marked for
deletion):

    python pwb.py imagecopy -page:Image:<imagename> -delete

By default the bot works on your home wiki (set in user-config)
"""
#
# (C) Pywikibot team, 2003-2021
#
# Distributed under the terms of the MIT license.
#
import codecs
import re
import threading
import webbrowser
from os import path

from requests.exceptions import RequestException

import pywikibot
from pywikibot import config, i18n, pagegenerators
from pywikibot.comms.http import fetch
from pywikibot.specialbots import UploadRobot
from pywikibot.tools import remove_last_args
from scripts.image import ImageRobot


try:
    from pywikibot.userinterfaces.gui import Tkdialog, Tkinter
except ImportError as _tk_error:
    Tkinter = _tk_error
    Tkdialog = object

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}

nowCommonsTemplate = {
    '_default': '{{NowCommons|%s}}',
    'af': '{{NowCommons|File:%s}}',
    'als': '{{NowCommons|%s}}',
    'am': '{{NowCommons|File:%s}}',
    'ang': '{{NowCommons|File:%s}}',
    'ar': '{{الآن كومنز|%s}}',
    'ary': '{{Now Commons|%s}}',
    'arz': '{{Now Commons|%s}}',
    'ast': '{{EnCommons|File:%s}}',
    'az': '{{NowCommons|%s}}',
    'bar': '{{NowCommons|%s}}',
    'bg': '{{NowCommons|%s}}',
    'bn': '{{NowCommons|File:%s}}',
    'bs': '{{NowCommons|%s}}',
    'ca': '{{AraCommons|%s}}',
    'cs': '{{NowCommons|%s}}',
    'cy': '{{NowCommons|File:%s}}',
    'da': '{{NowCommons|File:%s}}',
    'de': '{{NowCommons|%s}}',
    'dsb': '{{NowCommons|%s}}',
    'el': '{{NowCommons|%s}}',
    'en': '{{subst:ncd|%s}}',
    'eo': '{{Nun en komunejo|%s}}',
    'es': '{{EnCommons|File:%s}}',
    'et': '{{NüüdCommonsis|File:%s}}',
    'fa': '{{NowCommons|%s}}',
    'fi': '{{NowCommons|%s}}',
    'fo': '{{NowCommons|File:%s}}',
    'fr': '{{Image sur Commons|%s}}',
    'fy': '{{NowCommons|%s}}',
    'ga': '{{Ag Cómhaoin|File:%s}}',
    'gl': '{{EnCommons]|File:%s}}',
    'gv': '{{NowCommons|File:%s}}',
    'he': '{{גם בוויקישיתוף|%s}}',
    'hr': '{{NowCommons|%s}}',
    'hsb': '{{NowCommons|%s}}',
    'hu': '{{Azonnali-commons|%s}}',
    'ia': '{{NowCommons|File:%s}}',
    'id': '{{NowCommons|File:%s}}',
    'ilo': '{{NowCommons|File:%s}}',
    'io': '{{NowCommons|%s}}',
    'is': '{{NowCommons|%s}}',
    'it': '{{NowCommons|%s}}',
    'ja': '{{NowCommons|File:%s}}',
    'jv': '{{NowCommons|File:%s}}',
    'ka': '{{NowCommons|File:%s}}',
    'kn': '{{NowCommons|File:%s}}',
    'ko': '{{NowCommons|File:%s}}',
    'ku': '{{NowCommons|%s}}',
    'lb': '{{Elo op Commons|%s}}',
    'li': '{{NowCommons|%s}}',
    'lt': '{{NowCommons|File:%s}}',
    'lv': '{{NowCommons|File:%s}}',
    'mk': '{{NowCommons|File:%s}}',
    'mn': '{{NowCommons|File:%s}}',
    'ms': '{{NowCommons|%s}}',
    'nds-nl': '{{NoenCommons|File:%s}}',
    'nl': '{{NuCommons|%s}}',
    'nn': '{{No på Commons|File:%s}}',
    'no': '{{NowCommons|%s}}',
    'oc': '{{NowCommons|File:%s}}',
    'pl': '{{NowCommons|%s}}',
    'pt': '{{NowCommons|%s}}',
    'ro': '{{AcumCommons|File:%s}}',
    'ru': '{{Перенесено на Викисклад|%s}}',
    'sa': '{{NowCommons|File:%s}}',
    'scn': '{{NowCommons|File:%s}}',
    'sh': '{{NowCommons|File:%s}}',
    'sk': '{{NowCommons|File:%s}}',
    'sl': '{{OdslejZbirka|%s}}',
    'sq': '{{NowCommons|File:%s}}',
    'sr': '{{NowCommons|File:%s}}',
    'st': '{{NowCommons|File:%s}}',
    'su': '{{IlaharKiwari|File:%s}}',
    'sv': '{{NowCommons|%s}}',
    'sw': '{{NowCommons|%s}}',
    'ta': '{{NowCommons|File:%s}}',
    'th': '{{มีที่คอมมอนส์|File:%s}}',
    'tl': '{{NasaCommons|File:%s}}',
    'tr': '{{NowCommons|%s}}',
    'uk': '{{NowCommons|File:%s}}',
    'ur': '{{NowCommons|File:%s}}',
    'vec': '{{NowCommons|%s}}',
    'vi': '{{NowCommons|File:%s}}',
    'vo': '{{InKobädikos|%s}}',
    'wa': '{{NowCommons|%s}}',
    'zh': '{{NowCommons|File:%s}}',
    'zh-min-nan': '{{Commons ū|%s}}',
    'zh-yue': '{{subst:Ncd|File:%s}}',
}

moveToCommonsTemplate = {
    'ar': ['نقل إلى كومنز'],
    'en': ['Commons ok', 'Copy to Wikimedia Commons', 'Move to commons',
           'Movetocommons', 'To commons',
           'Copy to Wikimedia Commons by BotMultichill'],
    'fi': ['Commonsiin'],
    'fr': ['Image pour Commons'],
    'hsb': ['Kopěruj do Wikimedia Commons'],
    'hu': ['Commonsba'],
    'is': ['Færa á Commons'],
    'ms': ['Hantar ke Wikimedia Commons'],
    'nl': ['Verplaats naar Wikimedia Commons', 'VNC'],
    'pl': ['Do Commons', 'NaCommons', 'Na Commons'],
    'ru': ['На Викисклад'],
    'sl': ['Skopiraj v Zbirko'],
    'sr': ['За оставу', 'Пребацити на оставу'],
    'sv': ['Till Commons'],
    'zh': ['Copy to Wikimedia Commons'],
}


def pageTextPost(url, parameters):
    """
    Get data from commons helper page.

    :param url: This parameter is not used here, we keep it here to avoid user
                scripts from breaking.
    :param parameters: Data that will be submitted to CommonsHelper.
    :type parameters: dict
    :return: A CommonHelper description message.
    :rtype: str
    """
    while True:
        try:
            commonsHelperPage = fetch(
                'https://commonshelper.toolforge.org/',
                method='POST',
                data=parameters)
            data = commonsHelperPage.content.decode('utf-8')
            break
        except RequestException:
            pywikibot.output("Got a RequestException, let's try again")
    return data


class imageTransfer(threading.Thread):

    """Facilitate transfer of image/file to commons."""

    def __init__(self, imagePage, newname, category, delete_after_done=False):
        """Initializer."""
        self.imagePage = imagePage
        self.image_repo = imagePage.site.image_repository()
        self.newname = newname
        self.category = category
        self.delete_after_done = delete_after_done
        super().__init__()

    def run(self):
        """Run the bot."""
        tosend = {'language': self.imagePage.site.lang.encode('utf-8'),
                  'image': self.imagePage.title(
                      with_ns=False).encode('utf-8'),
                  'newname': self.newname.encode('utf-8'),
                  'project': self.imagePage.site.family.name.encode('utf-8'),
                  'username': '',
                  'commonsense': '1',
                  'remove_categories': '1',
                  'ignorewarnings': '1',
                  'doit': 'Uitvoeren'
                  }

        pywikibot.output(tosend)
        CH = pageTextPost('https://commonshelper.toolforge.org/index.php',
                          tosend)
        pywikibot.output('Got CH desc.')

        tablock = CH.split('<textarea ')[1].split('>')[0]
        CH = CH.split('<textarea ' + tablock + '>')[1].split('</textarea>')[0]
        CH = CH.replace('&times;', '×')
        CH = self.fixAuthor(CH)
        pywikibot.output(CH)

        # I want every picture to be tagged with the bottemplate so i can check
        # my contributions later.
        CH = ('\n\n{{BotMoveToCommons|%s.%s|year={{subst:CURRENTYEAR}}'
              '|month={{subst:CURRENTMONTHNAME}}|day={{subst:CURRENTDAY}}}}'
              % (self.imagePage.site.lang, self.imagePage.site.family.name)
              + CH)

        if self.category:
            CH = CH.replace(
                '{{subst:Unc}} <!-- Remove this line once you have '
                'added categories -->', '')
            CH += '[[Category:' + self.category + ']]'

        bot = UploadRobot(url=self.imagePage.get_file_url(), description=CH,
                          use_filename=self.newname, keep_filename=True,
                          verify_description=False, ignore_warning=True,
                          target_site=self.image_repo)
        bot.run()

        # Should check if the image actually was uploaded
        if pywikibot.Page(self.image_repo,
                          'Image:' + self.newname).exists():
            # Get a fresh copy, force to get the page so we don't run into edit
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
                {'localfile': self.imagePage.title(with_ns=False),
                 'commonsfile': self.newname})

            pywikibot.showDiff(self.imagePage.get(), imtxt + addTemplate)
            self.imagePage.put(imtxt + addTemplate, comment=commentText)

            self.gen = pagegenerators.FileLinksGenerator(self.imagePage)
            self.preloadingGen = pagegenerators.PreloadingGenerator(self.gen)

            moveSummary = i18n.twtranslate(
                self.imagePage.site,
                'commons-file-moved',
                {'localfile': self.imagePage.title(with_ns=False),
                 'commonsfile': self.newname})

            # If the image is uploaded under a different name, replace all
            # instances
            if self.imagePage.title(with_ns=False) != self.newname:
                imagebot = ImageRobot(
                    generator=self.preloadingGen,
                    oldImage=self.imagePage.title(with_ns=False),
                    newImage=self.newname,
                    summary=moveSummary, always=True, loose=True)
                imagebot.run()

            # If the user want to delete the page and
            # the user has sysops privilege, delete the page, otherwise
            # it will be marked for deletion.
            if self.delete_after_done:
                self.imagePage.delete(moveSummary, False)

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


def load_global_archivo():
    """Load/create Uploadbot.localskips.txt and save the path in `archivo`."""
    global archivo
    archivo = config.datafilepath('Uploadbot.localskips.txt')
    if not path.exists(archivo):
        with open(archivo, 'w') as tocreate:
            tocreate.write('{{NowCommons')


def getautoskip():
    """Get a list of templates to skip."""
    with codecs.open(archivo, 'r', 'utf-8') as f:
        txt = f.read()
    toreturn = txt.split('{{')[1:]
    return toreturn


class TkdialogIC(Tkdialog):

    """The dialog window for image info."""

    @remove_last_args(('commonsconflict',))
    def __init__(self, image_title, content, uploader, url, templates):
        """Initializer."""
        # Check if `Tkinter` wasn't imported
        if isinstance(Tkinter, ImportError):
            raise Tkinter

        super().__init__()
        self.root = Tkinter.Tk()
        # "%dx%d%+d%+d" % (width, height, xoffset, yoffset)
        # Always appear the same size and in the bottom-left corner
        self.root.geometry('600x200+100-100')
        self.root.title(image_title)
        self.changename = ''
        self.skip = 0
        self.url = url
        self.uploader = 'Unknown'
        # uploader.decode('utf-8')
        scrollbar = Tkinter.Scrollbar(self.root, orient=Tkinter.VERTICAL)
        label = Tkinter.Label(self.root, text='Enter new name or leave blank.')
        imageinfo = Tkinter.Label(self.root, text='Uploaded by {}.'.format(
            uploader))
        textarea = Tkinter.Text(self.root)
        textarea.insert(Tkinter.END, content.encode('utf-8'))
        textarea.config(state=Tkinter.DISABLED,
                        height=8, width=40, padx=0, pady=0,
                        wrap=Tkinter.WORD, yscrollcommand=scrollbar.set)
        scrollbar.config(command=textarea.yview)
        self.entry = Tkinter.Entry(self.root)

        self.templatelist = Tkinter.Listbox(self.root, bg='white', height=5)

        for template in templates:
            self.templatelist.insert(Tkinter.END, template)
        autoskip_button = Tkinter.Button(self.root, text='Add to AutoSkip',
                                         command=self.add2_auto_skip)
        browser_button = Tkinter.Button(self.root, text='View in browser',
                                        command=self.open_in_browser)
        skip_button = Tkinter.Button(self.root, text='Skip',
                                     command=self.skip_file)
        ok_button = Tkinter.Button(self.root, text='OK', command=self.ok_file)

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

        :return: new name and if the image is skipped
        :rtype: tuple
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
    always = False
    category = ''
    delete_after_done = False
    # Load a lot of default generators
    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        if arg == '-always':
            always = True
        elif arg.startswith('-setcat:'):
            category = arg[len('-setcat:'):]
        elif arg == '-delete':
            delete_after_done = True
        else:
            genFactory.handle_arg(arg)

    pregenerator = genFactory.getCombinedGenerator(preload=True)
    if not pregenerator:
        pywikibot.bot.suggest_help(missing_generator=True)
        return

    load_global_archivo()

    for page in pregenerator:
        if not page.exists() or page.namespace() != 6 or page.isRedirectPage():
            continue

        imagepage = pywikibot.FilePage(page.site, page.title())

        # First do autoskip.
        if doiskip(imagepage.get()):
            pywikibot.output('Skipping ' + page.title())
            continue

        # The first upload is last in the list.
        try:
            username = imagepage.latest_file_info.user
        except NotImplementedError:
            # No API, using the page file instead
            (datetime, username, resolution, size,
             comment) = imagepage.get_file_history().pop()

        skip = False
        if always:
            newname = imagepage.title(with_ns=False)
            CommonsPage = pywikibot.Page(pywikibot.Site('commons',
                                                        'commons'),
                                         'File:' + newname)
            if CommonsPage.exists():
                continue
        else:
            while True:
                # Do TkdialogIC to accept/reject and change the name
                newname, skip = TkdialogIC(
                    imagepage.title(with_ns=False),
                    imagepage.get(), username,
                    imagepage.permalink(with_protocol=True),
                    imagepage.templates()).getnewname()

                if skip:
                    pywikibot.output('Skipping this image')
                    break

                # Did we enter a new name?
                if not newname:
                    # Take the old name
                    newname = imagepage.title(with_ns=False)
                else:
                    newname = newname.decode('utf-8')

                # Check if the image already exists
                CommonsPage = pywikibot.Page(
                    imagepage.site.image_repository(),
                    'File:' + newname)

                if not CommonsPage.exists():
                    break

                pywikibot.output(
                    'Image already exists, pick another name or '
                    'skip this image')
                # We don't overwrite images, pick another name, go to
                # the start of the loop

        if not skip:
            imageTransfer(imagepage, newname, category,
                          delete_after_done).start()

    pywikibot.output('Still ' + str(threading.activeCount())
                     + ' active threads, lets wait')
    for openthread in threading.enumerate():
        if openthread != threading.currentThread():
            openthread.join()
    pywikibot.output('All threads are done')


if __name__ == '__main__':
    main()
