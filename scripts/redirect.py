#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script to resolve double redirects, and to delete broken redirects.

Requires access to MediaWiki's maintenance pages or to a XML dump file.
Delete function requires adminship.

Syntax:

    python pwb.py redirect action [-arguments ...]

where action can be one of these

:double:       Shortcut: **do**. Fix redirects which point to other redirects.

:broken:       Shortcut: **br**. Tries to fix redirect which point to nowhere
               by using the last moved target of the destination page. If this
               fails and the -delete option is set, it either deletes the page
               or marks it for deletion depending on whether the account has
               admin rights. It will mark the redirect not for deletion if
               there is no speedy deletion template available.

:both:         Both of the above. Retrieves redirect pages from live wiki,
               not from a special page.

and arguments can be:

-xml           Retrieve information from a local XML dump
               (https://dumps.wikimedia.org). Argument can also be given as
               "-xml:filename.xml". Cannot be used with -fullscan or -moves.

-fullscan      Retrieve redirect pages from live wiki, not from a special page
               Cannot be used with -xml.

-moves         Use the page move log to find double-redirect candidates. Only
               works with action "double", does not work with -xml.

               NOTE: You may use only one of these options above.
               If neither of -xml -fullscan -moves is given, info will be
               loaded from a special page of the live wiki.

-page:title    Work on a single page

-namespace:n   Namespace to process. Can be given multiple times, for several
               namespaces. If omitted, only the main (article) namespace is
               treated.

-offset:n      With -moves, the number of hours ago to start scanning moved
               pages. With -xml, the number of the redirect to restart with
               (see progress). Otherwise, ignored.

-start:title   The starting page title in each namespace. Page need not exist.

-until:title   The possible last page title in each namespace. Page needs not
               exist.

-limit:n       The maximum count of redirects to work upon. If omitted, there
               is no limit.

-delete        Prompt the user whether broken redirects should be deleted (or
               marked for deletion if the account has no admin rights) instead
               of just skipping them.

-sdtemplate:x  Add the speedy deletion template string including brackets.
               This enables overriding the default template via i18n or
               to enable speedy deletion for projects other than wikipedias.

-always        Don't prompt you for each replacement.

"""
#
# (C) Daniel Herding, 2004
# (C) Purodha Blissenbach, 2009
# (C) xqt, 2009-2020
# (C) Pywikibot team, 2004-2020
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import datetime

import pywikibot

from pywikibot import i18n, xmlreader
from pywikibot.bot import (OptionHandler, SingleSiteBot, ExistingPageBot,
                           RedirectPageBot)
from pywikibot.exceptions import ArgumentDeprecationWarning
from pywikibot.textlib import extract_templates_and_params_regex_simple
from pywikibot.tools import issue_deprecation_warning, UnicodeType


def space_to_underscore(link):
    """Convert spaces to underscore."""
    # previous versions weren't expecting spaces but underscores
    return link.canonical_title().replace(' ', '_')


class RedirectGenerator(OptionHandler):

    """Redirect generator."""

    availableOptions = {
        'fullscan': False,
        'moves': False,
        'namespaces': {0},
        'offset': -1,
        'page': None,
        'start': None,
        'limit': None,
        'until': None,
        'xml': None,
    }

    def __init__(self, action, **kwargs):
        """Initializer."""
        super(RedirectGenerator, self).__init__(**kwargs)
        self.site = pywikibot.Site()
        self.use_api = self.getOption('fullscan')
        self.use_move_log = self.getOption('moves')
        self.namespaces = self.getOption('namespaces')
        self.offset = self.getOption('offset')
        self.page_title = self.getOption('page')
        self.api_start = self.getOption('start')
        self.api_number = self.getOption('limit')
        self.api_until = self.getOption('until')
        self.xmlFilename = self.getOption('xml')

        # connect the generator selected by 'action' parameter
        cls = self.__class__
        if action == 'double':
            cls.__iter__ = lambda slf: slf.retrieve_double_redirects()
        elif action == 'broken':
            cls.__iter__ = lambda slf: slf.retrieve_broken_redirects()
        elif action == 'both':
            cls.__iter__ = lambda slf: slf.get_redirects_via_api(maxlen=2)

    def get_redirects_from_dump(self, alsoGetPageTitles=False):
        """
        Extract redirects from dump.

        Load a local XML dump file, look at all pages which have the
        redirect flag set, and find out where they're pointing at. Return
        a dictionary where the redirect names are the keys and the redirect
        targets are the values.
        """
        xmlFilename = self.xmlFilename
        redict = {}
        # open xml dump and read page titles out of it
        dump = xmlreader.XmlDump(xmlFilename)
        redirR = self.site.redirectRegex()
        readPagesCount = 0
        if alsoGetPageTitles:
            pageTitles = set()
        for entry in dump.parse():
            readPagesCount += 1
            # always print status message after 10000 pages
            if readPagesCount % 10000 == 0:
                pywikibot.output('{0} pages read...'.format(readPagesCount))
            if len(self.namespaces) > 0:
                if pywikibot.Page(self.site, entry.title).namespace() \
                        not in self.namespaces:
                    continue
            if alsoGetPageTitles:
                pageTitles.add(space_to_underscore(pywikibot.Link(entry.title,
                                                                  self.site)))

            m = redirR.match(entry.text)
            if m:
                target = m.group(1)
                # There might be redirects to another wiki. Ignore these.
                target_link = pywikibot.Link(target, self.site)
                try:
                    target_link.parse()
                except pywikibot.SiteDefinitionError as e:
                    pywikibot.log(e)
                    pywikibot.output(
                        'NOTE: Ignoring {0} which is a redirect ({1}) to an '
                        'unknown site.'.format(entry.title, target))
                    target_link = None
                else:
                    if target_link.site != self.site:
                        pywikibot.output(
                            'NOTE: Ignoring {0} which is a redirect to '
                            'another site {1}.'
                            .format(entry.title, target_link.site))
                        target_link = None
                # if the redirect does not link to another wiki
                if target_link and target_link.title:
                    source = pywikibot.Link(entry.title, self.site)
                    if target_link.anchor:
                        pywikibot.output(
                            'HINT: {0} is a redirect with a pipelink.'
                            .format(entry.title))
                    redict[space_to_underscore(source)] = (
                        space_to_underscore(target_link))
        if alsoGetPageTitles:
            return redict, pageTitles
        else:
            return redict

    def get_redirect_pages_via_api(self):
        """Yield Pages that are redirects."""
        for ns in self.namespaces:
            gen = self.site.allpages(start=self.api_start,
                                     namespace=ns,
                                     filterredir=True)
            if self.api_number:
                gen.set_maximum_items(self.api_number)
            for p in gen:
                done = (self.api_until
                        and p.title(with_ns=False) >= self.api_until)
                if done:
                    return
                yield p

    def _next_redirect_group(self):
        """Generator that yields batches of 500 redirects as a list."""
        apiQ = []
        for page in self.get_redirect_pages_via_api():
            apiQ.append(str(page.pageid))
            if len(apiQ) >= 500:
                pywikibot.output('.', newline=False)
                yield apiQ
                apiQ = []
        if apiQ:
            yield apiQ

    def get_redirects_via_api(self, maxlen=8):
        r"""
        Return a generator that yields tuples of data about redirect Pages.

        The description of returned tuple items is as follows:

        :[0]: page title of a redirect page
        :[1]: type of redirect:

             :None: start of a redirect chain of unknown length, or loop
             :[0]: broken redirect, target page title missing
             :[1]: normal redirect, target page exists and is not a
                          redirect
             :[2\:maxlen]: start of a redirect chain of that many redirects
                           (currently, the API seems not to return sufficient
                           data to make these return values possible, but
                           that may change)
             :[maxlen+1]: start of an even longer chain, or a loop
                          (currently, the API seems not to return sufficient
                          data to allow this return values, but that may
                          change)

        :[2]: target page title of the redirect, or chain (may not exist)
        :[3]: target page of the redirect, or end of chain, or page title
              where chain or loop detecton was halted, or None if unknown
        """
        for apiQ in self._next_redirect_group():
            gen = pywikibot.data.api.Request(
                site=self.site, parameters={'action': 'query',
                                            'redirects': True,
                                            'pageids': apiQ})
            data = gen.submit()
            if 'error' in data:
                raise RuntimeError('API query error: {0}'.format(data))
            if data == [] or 'query' not in data:
                raise RuntimeError('No results given.')
            pages = {}
            redirects = {x['from']: x['to']
                         for x in data['query']['redirects']}

            for pagetitle in data['query']['pages'].values():
                if 'missing' in pagetitle and 'pageid' not in pagetitle:
                    pages[pagetitle['title']] = False
                else:
                    pages[pagetitle['title']] = True
            for redirect in redirects:
                target = redirects[redirect]
                result = 0
                final = None
                try:
                    if pages[target]:
                        final = target
                        try:
                            while result <= maxlen:
                                result += 1
                                final = redirects[final]
                            # result = None
                        except KeyError:
                            pass
                except KeyError:
                    result = None
                yield (redirect, result, target, final)

    def retrieve_broken_redirects(self):
        """Retrieve broken redirects."""
        if self.use_api:
            count = 0
            for (pagetitle, type, target, final) \
                    in self.get_redirects_via_api(maxlen=2):
                if type == 0:
                    yield pagetitle
                    if self.api_number:
                        count += 1
                        if count >= self.api_number:
                            break
        elif self.xmlFilename:
            # retrieve information from XML dump
            pywikibot.output(
                'Getting a list of all redirects and of all page titles...')
            redirs, pageTitles = self.get_redirects_from_dump(
                alsoGetPageTitles=True)
            for (key, value) in redirs.items():
                if value not in pageTitles:
                    yield key
        elif self.page_title:
            yield self.page_title
        else:
            pywikibot.output('Retrieving broken redirect special page...')
            for page in self.site.preloadpages(self.site.broken_redirects()):
                yield page

    def retrieve_double_redirects(self):
        """Retrieve double redirects."""
        if self.use_move_log:
            for redir_page in self.get_moved_pages_redirects():
                yield redir_page
        elif self.use_api:
            count = 0
            for (pagetitle, type, target, final) \
                    in self.get_redirects_via_api(maxlen=2):
                if type != 0 and type != 1:
                    yield pagetitle
                    if self.api_number:
                        count += 1
                        if count >= self.api_number:
                            break
        elif self.xmlFilename:
            redict = self.get_redirects_from_dump()
            total = len(redict)
            for num, (key, value) in enumerate(redict.items(), start=1):
                # check if the value - that is, the redirect target - is a
                # redirect as well
                if num > self.offset and value in redict:
                    pywikibot.output('\nChecking redirect {0} of {1}...'
                                     .format(num, total))
                    yield key
        elif self.page_title:
            yield self.page_title
        else:
            pywikibot.output('Retrieving double redirect special page...')
            for page in self.site.preloadpages(self.site.double_redirects()):
                yield page

    def get_moved_pages_redirects(self):
        """Generate redirects to recently-moved pages."""
        # this will run forever, until user interrupts it
        if self.offset <= 0:
            self.offset = 1
        start = (datetime.datetime.utcnow()
                 - datetime.timedelta(0, self.offset * 3600))
        # self.offset hours ago
        offset_time = start.strftime('%Y%m%d%H%M%S')
        pywikibot.output('Retrieving {0} moved pages...'
                         ''.format(str(self.api_number)
                                   if self.api_number is not None else 'all'))
        move_gen = self.site.logevents(logtype='move', start=offset_time)
        if self.api_number:
            move_gen.set_maximum_items(self.api_number)
        pywikibot.output('.', newline=False)
        for logentry in move_gen:
            try:
                moved_page = logentry.page()
            except KeyError:  # hidden page
                continue
            pywikibot.output('.', newline=False)
            try:
                if not moved_page.isRedirectPage():
                    continue
            except pywikibot.BadTitle:
                continue
            except pywikibot.ServerError:
                continue
            # moved_page is now a redirect, so any redirects pointing
            # to it need to be changed
            try:
                for page in moved_page.getReferences(follow_redirects=True,
                                                     filter_redirects=True):
                    yield page
            except pywikibot.NoPage:
                # original title must have been deleted after move
                continue
            except pywikibot.CircularRedirect:
                continue
            except pywikibot.InterwikiRedirectPage:
                continue


class RedirectRobot(SingleSiteBot, ExistingPageBot, RedirectPageBot):

    """Redirect bot."""

    def __init__(self, action, **kwargs):
        """Initializer."""
        self.availableOptions.update({
            'limit': float('inf'),
            'delete': False,
            'sdtemplate': None,
        })
        super(RedirectRobot, self).__init__(**kwargs)
        self.repo = self.site.data_repository()
        self.is_repo = self.repo if self.repo == self.site else None
        self.sdtemplate = self.get_sd_template()

        # connect the action treat to treat_page method called by treat
        if action == 'double':
            self.treat_page = self.fix_1_double_redirect
        elif action == 'broken':
            self.treat_page = self.delete_1_broken_redirect
        elif action == 'both':
            self.treat_page = self.fix_double_or_delete_broken_redirect
        else:
            raise NotImplementedError('No valid action "{0}" found.'
                                      ''.format(action))

    def get_sd_template(self):
        """Look for speedy deletion template and return it.

        @return: A valid speedy deletion template.
        @rtype: str or None
        """
        if self.getOption('delete') and not self.site.has_right('delete'):
            sd = self.getOption('sdtemplate')
            if not sd and i18n.twhas_key(self.site,
                                         'redirect-broken-redirect-template'):
                sd = i18n.twtranslate(self.site,
                                      'redirect-broken-redirect-template')
            # TODO: Add bot's signature if needed (Bug: T131517)

            # check whether template exists for this site
            title = None
            if sd:
                template = extract_templates_and_params_regex_simple(sd)
                if template:
                    title = template[0][0]
                    page = pywikibot.Page(self.site, title, ns=10)
                    if page.exists():
                        return sd
            pywikibot.warning(
                'No speedy deletion template {0}available.'
                ''.format('"{0}" '.format(title) if title else ''))
        return None

    def init_page(self, item):
        """Ensure that we process page objects."""
        if isinstance(item, UnicodeType):
            item = pywikibot.Page(self.site, item)
        elif isinstance(item, tuple):
            redir_name, code, target, final = item
            item = pywikibot.Page(self.site, redir_name)
            item._redirect_type = code
        return super(RedirectRobot, self).init_page(item)

    def delete_redirect(self, page, summary_key):
        """Delete the redirect page."""
        assert page.site == self.site, (
            'target page is on different site {0}'.format(page.site))
        reason = i18n.twtranslate(self.site, summary_key)
        if page.site.has_right('delete'):
            page.delete(reason, prompt=False)
        elif self.sdtemplate:
            pywikibot.output('User does not have delete right, '
                             'put page to speedy deletion.')
            try:
                content = page.get(get_redirect=True)
            except pywikibot.SectionError:
                content_page = pywikibot.Page(page.site,
                                              page.title(with_section=False))
                content = content_page.get(get_redirect=True)
            content = self.sdtemplate + '\n' + content
            self.userPut(page, page.text, content, summary=reason,
                         ignore_save_related_errors=True,
                         ignore_server_errors=True)

    def delete_1_broken_redirect(self):
        """Treat one broken redirect."""
        redir_page = self.current_page
        done = not self.getOption('delete')
        try:
            targetPage = redir_page.getRedirectTarget()
        except (pywikibot.CircularRedirect,
                pywikibot.InvalidTitle,
                RuntimeError):
            pywikibot.exception()
        except pywikibot.InterwikiRedirectPage:
            pywikibot.output('{0} is on another site.'
                             .format(redir_page.title()))
        else:
            try:
                targetPage.get()
            except pywikibot.BadTitle as e:
                pywikibot.warning(
                    'Redirect target {0} is not a valid page title.'
                    .format(str(e)[10:]))
            except pywikibot.InvalidTitle:
                pywikibot.exception()
            except pywikibot.NoPage:
                movedTarget = None
                try:
                    movedTarget = targetPage.moved_target()
                except pywikibot.NoMoveTarget:
                    pass
                if movedTarget:
                    if not movedTarget.exists():
                        # FIXME: Test to another move
                        pywikibot.output('Target page {0} does not exist'
                                         .format(movedTarget))
                    elif redir_page == movedTarget:
                        pywikibot.output(
                            'Redirect to target page forms a redirect loop')
                    else:
                        pywikibot.output('{0} has been moved to {1}'
                                         .format(redir_page, movedTarget))
                        reason = i18n.twtranslate(self.site,
                                                  'redirect-fix-broken-moved',
                                                  {'to': movedTarget.title(
                                                      as_link=True)})
                        content = redir_page.get(get_redirect=True)
                        redir_page.set_redirect_target(
                            movedTarget, keep_section=True, save=False)
                        pywikibot.output('Summary - ' + reason)
                        done = self.userPut(redir_page, content,
                                            redir_page.text, summary=reason,
                                            ignore_save_related_errors=True,
                                            ignore_server_errors=True)
                if not done and self.user_confirm(
                        'Redirect target {0} does not exist.\n'
                        'Do you want to delete {1}?'
                        .format(targetPage.title(as_link=True),
                                redir_page.title(as_link=True))):
                    self.delete_redirect(redir_page, 'redirect-remove-broken')
                elif not (self.getOption('delete') or movedTarget):
                    pywikibot.output(
                        'Cannot fix or delete the broken redirect')
            except pywikibot.IsRedirectPage:
                pywikibot.output(
                    'Redirect target {0} is also a redirect! {1}'.format(
                        targetPage.title(as_link=True),
                        "Won't delete anything."
                        if self.getOption('delete') else 'Skipping.'))
            else:
                # we successfully get the target page, meaning that
                # it exists and is not a redirect: no reason to touch it.
                pywikibot.output(
                    'Redirect target {0} does exist! {1}'.format(
                        targetPage.title(as_link=True),
                        "Won't delete anything."
                        if self.getOption('delete') else 'Skipping.'))

    def fix_1_double_redirect(self):
        """Treat one double redirect."""
        newRedir = redir = self.current_page
        redirList = []  # bookkeeping to detect loops
        while True:
            redirList.append('{0}:{1}'
                             .format(newRedir.site.lang,
                                     newRedir.title(with_section=False)))
            try:
                targetPage = newRedir.getRedirectTarget()
            except pywikibot.IsNotRedirectPage:
                if len(redirList) == 2:
                    pywikibot.output(
                        'Skipping: Redirect target {0} is not a redirect.'
                        .format(newRedir.title(as_link=True)))
                    break  # do nothing
            except pywikibot.SectionError:
                pywikibot.warning(
                    "Redirect target section {0} doesn't exist."
                    .format(newRedir.title(as_link=True)))
            except (pywikibot.CircularRedirect,
                    pywikibot.InterwikiRedirectPage,
                    pywikibot.UnsupportedPage,
                    RuntimeError):
                pywikibot.exception()
                pywikibot.output('Skipping {0}.'.format(newRedir))
                break
            except pywikibot.BadTitle as e:
                # str(e) is in the format 'BadTitle: [[Foo]]'
                pywikibot.warning(
                    'Redirect target {0} is not a valid page title.'
                    .format(str(e)[10:]))
                break
            except pywikibot.NoPage:
                if self.getOption('always'):
                    pywikibot.output(
                        "Skipping: Redirect target {} doesn't exist."
                        .format(newRedir.title(as_link=True)))
                    break  # skip if automatic
                else:
                    pywikibot.warning(
                        "Redirect target {} doesn't exist."
                        .format(newRedir.title(as_link=True)))
            except pywikibot.ServerError:
                pywikibot.output('Skipping due to server error: '
                                 'No textarea found')
                break
            else:
                pywikibot.output(
                    '   Links to: {0}.'
                    .format(targetPage.title(as_link=True)))
                try:
                    mw_msg = targetPage.site.mediawiki_message(
                        'wikieditor-toolbar-tool-redirect-example')
                except KeyError:
                    pass
                else:
                    if targetPage.title() == mw_msg:
                        pywikibot.output(
                            'Skipping toolbar example: Redirect source is '
                            'potentially vandalized.')
                        break
                # watch out for redirect loops
                if redirList.count('{0}:{1}'.format(
                    targetPage.site.lang,
                        targetPage.title(with_section=False))):
                    pywikibot.warning(
                        'Redirect target {0} forms a redirect loop.'
                        .format(targetPage.title(as_link=True)))
                    break  # FIXME: doesn't work. edits twice!
                    if self.getOption('delete'):
                        # Delete the two redirects
                        # TODO: Check whether pages aren't vandalized
                        # and (maybe) do not have a version history
                        self.delete_redirect(targetPage,
                                             'redirect-remove-loop')
                        self.delete_redirect(redir, 'redirect-remove-loop')
                    break
                else:  # redirect target found
                    if targetPage.isStaticRedirect():
                        pywikibot.output(
                            '   Redirect target is STATICREDIRECT.')
                    else:
                        newRedir = targetPage
                        continue
            try:
                oldText = redir.get(get_redirect=True)
            except pywikibot.BadTitle:
                pywikibot.output('Bad Title Error')
                break
            if self.is_repo and redir.namespace() == self.repo.item_namespace:
                redir = pywikibot.ItemPage(self.repo, redir.title())
                targetPage = pywikibot.ItemPage(self.repo, targetPage.title())
                pywikibot.output('Fixing double item redirect')
                redir.set_redirect_target(targetPage)
                break
            redir.set_redirect_target(targetPage, keep_section=True,
                                      save=False)
            summary = i18n.twtranslate(self.site, 'redirect-fix-double',
                                       {'to': targetPage.title(as_link=True)}
                                       )
            self.userPut(redir, oldText, redir.text, summary=summary,
                         ignore_save_related_errors=True,
                         ignore_server_errors=True)
            break

    def fix_double_or_delete_broken_redirect(self):
        """Treat one broken or double redirect."""
        if self.current_page._redirect_type == 0:
            self.delete_1_broken_redirect()
        elif self.current_page._redirect_type != 1:
            self.fix_1_double_redirect()

    def treat(self, page):
        """Treat a page."""
        if self._treat_counter >= self.getOption('limit'):
            pywikibot.output('\nNumber of pages reached the limit. '
                             'Script terminated.')
            self.stop()
        super(RedirectRobot, self).treat(page)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: str
    """
    options = {}
    gen_options = {}
    # what the bot should do (either resolve double redirs, or process broken
    # redirs)
    action = None
    namespaces = set()
    source = set()

    for arg in pywikibot.handle_args(args):
        arg, sep, value = arg.partition(':')
        option = arg.partition('-')[2]
        # bot options
        if arg == 'do':
            action = 'double'
        elif arg == 'br':
            action = 'broken'
        elif arg in ('both', 'broken', 'double'):
            action = arg
        elif option in ('always', 'delete'):
            options[option] = True
        elif option == 'sdtemplate':
            options['sdtemplate'] = value or pywikibot.input(
                'Which speedy deletion template to use?')
        # generator options
        elif option in ('fullscan', 'moves'):
            gen_options[option] = True
            source.add(arg)
        elif option == 'xml':
            gen_options[option] = value or i18n.input(
                'pywikibot-enter-xml-filename')
            source.add(arg)
        elif option == 'namespace':
            # "-namespace:" does NOT yield -namespace:0 further down the road!
            ns = value or i18n.input('pywikibot-enter-namespace-number')
            # TODO: at least for some generators enter a namespace by its name
            # or number
            if ns == '':
                ns = '0'
            try:
                ns = int(ns)
            except ValueError:
                # -namespace:all Process all namespaces.
                # Only works with the API read interface.
                pass
            else:
                namespaces.add(ns)
        elif option == 'offset':
            gen_options[option] = int(value)
        elif option in ('page', 'start', 'until'):
            gen_options[option] = value
        elif option in ('limit', 'total'):
            options['limit'] = gen_options['limit'] = int(value)
            if option == 'total':
                issue_deprecation_warning('The usage of "{0}"'.format(arg),
                                          '-limit', 2,
                                          ArgumentDeprecationWarning,
                                          since='20190120')
        else:
            pywikibot.output('Unknown argument: ' + arg)

    if namespaces:
        gen_options['namespaces'] = namespaces

    if len(source) > 1:
        problem = 'You can only use one of {0} options.'.format(
            ' or '.join(source))
        pywikibot.bot.suggest_help(additional_text=problem,
                                   missing_action=not action)
        return
    if not action:
        pywikibot.bot.suggest_help(missing_action=True)
    else:
        pywikibot.Site().login()
        options['generator'] = RedirectGenerator(action, **gen_options)
        bot = RedirectRobot(action, **options)
        bot.run()


if __name__ == '__main__':
    main()
