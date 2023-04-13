#!/usr/bin/env python3
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
               Cannot be used with -xml or 'both' action.

-moves         Use the page move log to find double-redirect candidates. Only
               works with action "double", does not work with -xml.

               NOTE: You may use only one of these options above.
               If neither of -xml -fullscan -moves is given, info will be
               loaded from a special page of the live wiki.

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
               to enable speedy deletion for projects other than Wikipedias.

-always        Don't prompt you for each replacement.

Furthermore the following options are provided:

&params;
"""
#
# (C) Pywikibot team, 2004-2023
#
# Distributed under the terms of the MIT license.
#
import datetime
from contextlib import suppress
from textwrap import fill
from typing import Any, Generator, Optional, Union

import pywikibot
import pywikibot.data
from pywikibot import i18n, pagegenerators, xmlreader
from pywikibot.backports import Dict, List, Set, Tuple
from pywikibot.bot import ExistingPageBot, OptionHandler, suggest_help
from pywikibot.exceptions import (
    CircularRedirectError,
    InterwikiRedirectPageError,
    InvalidTitleError,
    IsNotRedirectPageError,
    IsRedirectPageError,
    NoMoveTargetError,
    NoPageError,
    SectionError,
    ServerError,
    SiteDefinitionError,
    UnsupportedPageError,
)
from pywikibot.textlib import extract_templates_and_params_regex_simple


docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816


def space_to_underscore(link) -> str:
    """Convert spaces to underscore."""
    # previous versions weren't expecting spaces but underscores
    return link.canonical_title().replace(' ', '_')


class RedirectGenerator(OptionHandler):

    """Redirect generator."""

    available_options = {
        'fullscan': False,
        'moves': False,
        'namespaces': {0},
        'offset': -1,
        'start': None,
        'limit': None,
        'until': None,
        'xml': None,
    }

    def __init__(self, action, **kwargs) -> None:
        """Initializer."""
        super().__init__(**kwargs)
        self.site = pywikibot.Site()

        # connect the generator selected by 'action' parameter
        cls = self.__class__
        if action == 'double':
            cls.__iter__ = lambda slf: slf.retrieve_double_redirects()
        elif action == 'broken':
            cls.__iter__ = lambda slf: slf.retrieve_broken_redirects()
        elif action == 'both':
            cls.__iter__ = lambda slf: slf.get_redirects_via_api(maxlen=2)

    def get_redirects_from_dump(
        self,
        alsoGetPageTitles: bool = False
    ) -> Tuple[Dict[str, str], Set[str]]:
        """
        Extract redirects from dump.

        Load a local XML dump file, look at all pages which have the
        redirect flag set, and find out where they're pointing at. Return
        a dictionary where the redirect names are the keys and the redirect
        targets are the values.
        """
        xmlFilename = self.opt.xml
        redict = {}
        # open xml dump and read page titles out of it
        dump = xmlreader.XmlDump(xmlFilename, on_error=pywikibot.error)
        redirR = self.site.redirect_regex
        readPagesCount = 0
        pageTitles = set()
        for entry in dump.parse():
            readPagesCount += 1
            # always print status message after 10000 pages
            if readPagesCount % 10000 == 0:
                pywikibot.info(f'{readPagesCount} pages read...')
            if self.opt.namespaces and pywikibot.Page(
                    self.site,
                    entry.title).namespace() not in self.opt.namespaces:
                continue

            if alsoGetPageTitles:
                pageTitles.add(space_to_underscore(pywikibot.Link(entry.title,
                                                                  self.site)))

            m = redirR.match(entry.text)
            if m:
                target = m[1]
                # There might be redirects to another wiki. Ignore these.
                target_link = pywikibot.Link(target, self.site)
                try:
                    target_link.parse()
                except SiteDefinitionError as e:
                    pywikibot.log(e)
                    pywikibot.info(
                        'NOTE: Ignoring {} which is a redirect ({}) to an '
                        'unknown site.'.format(entry.title, target))
                    target_link = None
                else:
                    if target_link.site != self.site:
                        pywikibot.info(
                            'NOTE: Ignoring {} which is a redirect to '
                            'another site {}.'
                            .format(entry.title, target_link.site))
                        target_link = None
                # if the redirect does not link to another wiki
                if target_link and target_link.title:
                    source = pywikibot.Link(entry.title, self.site)
                    if target_link.anchor:
                        pywikibot.info(
                            'HINT: {} is a redirect with a pipelink.'
                            .format(entry.title))
                    redict[space_to_underscore(source)] = (
                        space_to_underscore(target_link))
        return redict, pageTitles

    def get_redirect_pages_via_api(self) -> Generator[pywikibot.Page, None,
                                                      None]:
        """Yield Pages that are redirects."""
        for ns in self.opt.namespaces:
            gen = self.site.allpages(start=self.opt.start,
                                     namespace=ns,
                                     filterredir=True)
            if self.opt.limit:
                gen.set_maximum_items(self.opt.limit)
            for p in gen:
                done = (self.opt.until
                        and p.title(with_ns=False) >= self.opt.until)
                if done:
                    return
                yield p

    def _next_redirect_group(self) -> Generator[List[pywikibot.Page], None,
                                                None]:
        """Generator that yields batches of redirects as a list."""
        chunk = []
        for page in self.get_redirect_pages_via_api():
            chunk.append(str(page.pageid))
            if len(chunk) >= self.site.maxlimit:
                pywikibot.info('.', newline=False)
                yield chunk
                chunk.clear()
        if chunk:
            yield chunk

    def get_redirects_via_api(
        self,
        maxlen: int = 8
    ) -> Generator[Tuple[str, Optional[int], str, Optional[str]], None, None]:
        r"""
        Return a generator that yields tuples of data about redirect Pages.

        .. versionchanged:: 7.0
           only yield tuple if type of redirect is not 1 (normal redirect)

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
                raise RuntimeError(f'API query error: {data}')
            if data == [] or 'query' not in data:
                raise RuntimeError('No results given.')
            pages = {}
            redirects = {x['from']: x['to']
                         for x in data['query']['redirects']}

            for pagetitle in data['query']['pages'].values():
                pages[pagetitle['title']] = \
                    'missing' not in pagetitle or 'pageid' in pagetitle

            for redirect, target in redirects.items():
                result = None
                final = None

                if pages.get(target):
                    result = 0
                    final = target
                    with suppress(KeyError):
                        while result <= maxlen:
                            result += 1
                            final = redirects[final]

                # only yield multiple or broken redirects
                if result != 1:
                    yield redirect, result, target, final

    def retrieve_broken_redirects(self) -> Generator[
            Union[str, pywikibot.Page], None, None]:
        """Retrieve broken redirects."""
        if self.opt.fullscan:
            count = 0
            for pagetitle, type_, *_ in self.get_redirects_via_api(maxlen=2):
                if type_ == 0:
                    yield pagetitle
                    count += 1
                    if self.opt.limit and count >= self.opt.limit:
                        break
        elif self.opt.xml:
            # retrieve information from XML dump
            pywikibot.info(
                'Getting a list of all redirects and of all page titles...')
            redirs, pageTitles = self.get_redirects_from_dump(
                alsoGetPageTitles=True)
            for (key, value) in redirs.items():
                if value not in pageTitles:
                    yield key
        else:
            pywikibot.info('Retrieving broken redirect special page...')
            yield from self.site.preloadpages(self.site.broken_redirects())

    def retrieve_double_redirects(self) -> Generator[
            Union[str, pywikibot.Page], None, None]:
        """Retrieve double redirects."""
        if self.opt.moves:
            yield from self.get_moved_pages_redirects()
        elif self.opt.fullscan:
            count = 0
            for pagetitle, type_, *_ in self.get_redirects_via_api(maxlen=2):
                if type_ not in (0, 1):
                    yield pagetitle
                    count += 1
                    if self.opt.limit and count >= self.opt.limit:
                        break
        elif self.opt.xml:
            redict, _ = self.get_redirects_from_dump()
            total = len(redict)
            for num, (key, value) in enumerate(redict.items(), start=1):
                # check if the value - that is, the redirect target - is a
                # redirect as well
                if num > self.opt.offset and value in redict:
                    pywikibot.info(f'\nChecking redirect {num} of {total}...')
                    yield key
        else:
            pywikibot.info('Retrieving double redirect special page...')
            yield from self.site.preloadpages(self.site.double_redirects())

    def get_moved_pages_redirects(self) -> Generator[pywikibot.Page, None,
                                                     None]:
        """Generate redirects to recently-moved pages."""
        # this will run forever, until user interrupts it
        if self.opt.offset <= 0:
            self.opt.offset = 1
        start = (datetime.datetime.utcnow()
                 - datetime.timedelta(0, self.opt.offset * 3600))
        # self.opt.offset hours ago
        offset_time = start.strftime('%Y%m%d%H%M%S')
        pywikibot.info('Retrieving {} moved pages...'
                       .format(self.opt.limit
                               if self.opt.limit is not None else 'all'))
        move_gen = self.site.logevents(logtype='move', start=offset_time)
        if self.opt.limit:
            move_gen.set_maximum_items(self.opt.limit)
        pywikibot.info('.', newline=False)
        for logentry in move_gen:
            try:
                moved_page = logentry.page()
            except KeyError:  # hidden page
                continue
            pywikibot.info('.', newline=False)
            try:
                if not moved_page.isRedirectPage():
                    continue
            except ServerError:
                continue
            # moved_page is now a redirect, so any redirects pointing
            # to it need to be changed
            try:
                yield from moved_page.getReferences(follow_redirects=True,
                                                    filter_redirects=True)
            except (CircularRedirectError,
                    InterwikiRedirectPageError,
                    NoPageError,
                    ):
                continue


class RedirectRobot(ExistingPageBot):

    """Redirect bot."""

    use_redirects = True

    update_options = {
        'limit': float('inf'),
        'delete': False,
        'sdtemplate': '',
    }

    def __init__(self, action, **kwargs) -> None:
        """Initializer."""
        super().__init__(**kwargs)
        # connect the action treat to treat_page method called by treat
        if action == 'double':
            self.treat_page = self.fix_1_double_redirect
        elif action == 'broken':
            self.treat_page = self.delete_1_broken_redirect
        elif action == 'both':
            self.treat_page = self.fix_double_or_delete_broken_redirect
        else:
            raise NotImplementedError('No valid action "{}" found.'
                                      .format(action))

    def get_sd_template(self, site=None) -> Optional[str]:
        """Look for speedy deletion template and return it.

        :param site: site for which the template has to be given
        :type site: pywikibot.BaseSite
        :return: A valid speedy deletion template.
        """
        title = None
        if site:
            sd = self.opt.sdtemplate
            if not sd and i18n.twhas_key(site,
                                         'redirect-broken-redirect-template'):
                sd = i18n.twtranslate(site,
                                      'redirect-broken-redirect-template')

            # check whether template exists for this site
            if sd:
                template = extract_templates_and_params_regex_simple(sd)
                if template:
                    title = template[0][0]
                    page = pywikibot.Page(site, title, ns=10)
                    if page.exists():
                        return sd

        pywikibot.warning(
            'No speedy deletion template {}available.'
            .format(f'"{title}" ' if title else ''))
        return None

    @property
    def sdtemplate(self):
        """Gives the speedy deletion template for the current_page."""
        return self.get_sd_template(self.current_page.site)

    def init_page(self, item) -> pywikibot.Page:
        """Ensure that we process page objects."""
        default_site = pywikibot.Site()
        if isinstance(item, str):
            item = pywikibot.Page(default_site, item)
        elif isinstance(item, tuple):
            redir_name, code, *_ = item
            item = pywikibot.Page(default_site, redir_name)
            item._redirect_type = code
        page = super().init_page(item)
        self.repo = page.site.data_repository()
        self.is_repo = self.repo if self.repo == page.site else None
        return page

    def delete_redirect(self, page, summary_key: str) -> None:
        """Delete the redirect page.

        :param page: The page to delete
        :type page: pywikibot.page.BasePage
        :param summary_key: The message key for the deletion summary
        """
        assert page.site == self.current_page.site, (
            f'target page is on different site {page.site}')
        reason = i18n.twtranslate(page.site, summary_key, bot_prefix=True)
        if page.site.has_right('delete'):
            page.delete(reason, prompt=False)
        elif self.sdtemplate:
            pywikibot.info('User does not have delete right, '
                           'put page to speedy deletion.')
            try:
                content = page.get(get_redirect=True)
            except SectionError:
                content_page = pywikibot.Page(page.site,
                                              page.title(with_section=False))
                content = content_page.get(get_redirect=True)
            content = self.sdtemplate + '\n' + content
            self.userPut(page, page.text, content, summary=reason,
                         ignore_save_related_errors=True,
                         ignore_server_errors=True)

    @staticmethod
    def get_redirect_target(page):
        """Get redirect target page and handle some exceptions."""
        try:
            return page.getRedirectTarget()
        except (CircularRedirectError, RuntimeError) as e:
            pywikibot.error(e)
            pywikibot.info(f'Skipping {page}.')
        except InterwikiRedirectPageError:
            pywikibot.info(f'{page} is on another site, skipping.')
        return None

    def delete_1_broken_redirect(self) -> None:
        """Treat one broken redirect."""
        redir_page = self.current_page
        done = not self.opt.delete
        try:
            targetPage = self.get_redirect_target(redir_page)
        except InvalidTitleError as e:
            pywikibot.error(e)
            targetPage = None

        if not targetPage:
            return

        try:
            targetPage.get()
        except InvalidTitleError as e:
            pywikibot.error(e)
        except NoPageError:
            movedTarget = None
            with suppress(NoMoveTargetError):
                movedTarget = targetPage.moved_target()
            if movedTarget:
                if not movedTarget.exists():
                    # FIXME: Test to another move
                    pywikibot.info(f'Target page {movedTarget} does not exist')
                elif redir_page == movedTarget:
                    pywikibot.info(
                        'Redirect to target page forms a redirect loop')
                else:
                    pywikibot.info(
                        f'{redir_page} has been moved to {movedTarget}')
                    reason = i18n.twtranslate(
                        redir_page.site, 'redirect-fix-broken-moved',
                        {'to': movedTarget.title(as_link=True,
                                                 allow_interwiki=False)},
                        bot_prefix=True)
                    content = redir_page.get(get_redirect=True)
                    redir_page.set_redirect_target(
                        movedTarget, keep_section=True, save=False)
                    pywikibot.info('Summary - ' + reason)
                    done = self.userPut(redir_page, content,
                                        redir_page.text, summary=reason,
                                        ignore_save_related_errors=True,
                                        ignore_server_errors=True)
            if not done and self.user_confirm(
                    'Redirect target {} does not exist.\n'
                    'Do you want to delete {}?'
                    .format(targetPage.title(as_link=True),
                            redir_page.title(as_link=True))):
                self.delete_redirect(redir_page, 'redirect-remove-broken')
            elif not (self.opt.delete or movedTarget):
                pywikibot.info('Cannot fix or delete the broken redirect')
        except IsRedirectPageError:
            pywikibot.info(
                'Redirect target {} is also a redirect! {}'.format(
                    targetPage.title(as_link=True),
                    "Won't delete anything."
                    if self.opt.delete else 'Skipping.'))
        else:
            # we successfully get the target page, meaning that
            # it exists and is not a redirect: no reason to touch it.
            pywikibot.info('Redirect target {} does exist! {}'
                           .format(targetPage.title(as_link=True),
                                   "Won't delete anything."
                                   if self.opt.delete else 'Skipping.'))

    def _skip_on_exception(self,
                           error: Exception,
                           loop_length: int,
                           new_redir: pywikibot.Page) -> bool:
        """Handle exceptions of fix_1_double_redirect."""
        if isinstance(error, IsNotRedirectPageError):
            if loop_length != 2:
                return False  # do nothing

            pywikibot.info(
                f'Skipping: Redirect target {new_redir} is not a  redirect.')

        elif isinstance(error, SectionError):
            pywikibot.warning(
                f"Redirect target section {new_redir} doesn't exist.")
            return False

        elif isinstance(error, UnsupportedPageError):
            pywikibot.error(error)
            pywikibot.info(f'Skipping {new_redir}.')

        elif isinstance(error, NoPageError):
            if not self.opt.always:
                pywikibot.warning(
                    f"Redirect target {new_redir} doesn't exist.")
                return False

            # skip if automatic
            pywikibot.info(
                f"Skipping: Redirect target {new_redir} doesn't exist.")

        elif isinstance(error, ServerError):
            pywikibot.info('Skipping due to server error: No textarea found')

        else:
            # all uncatched exceptions
            # Note: elif statements are necessary above because all Errors
            # above derive from Exception class
            raise

        return True

    def fix_1_double_redirect(self) -> None:
        """Treat one double redirect."""
        newRedir = redir = self.current_page
        redirList = []  # bookkeeping to detect loops
        while True:
            redirList.append('{}:{}'
                             .format(newRedir.site.lang,
                                     newRedir.title(with_section=False)))
            try:
                targetPage = self.get_redirect_target(newRedir)
            except Exception as e:
                if self._skip_on_exception(e, len(redirList), newRedir):
                    break
            else:
                if not targetPage:
                    break

                pywikibot.info(f'   Links to: {targetPage}.')
                mw_msg = None
                with suppress(KeyError):
                    mw_msg = targetPage.site.mediawiki_message(
                        'wikieditor-toolbar-tool-redirect-example')
                if mw_msg and targetPage.title() == mw_msg:
                    pywikibot.info('Skipping toolbar example: Redirect source '
                                   'is potentially vandalized.')
                    break

                # watch out for redirect loops
                if redirList.count('{}:{}'.format(
                    targetPage.site.lang,
                        targetPage.title(with_section=False))):
                    pywikibot.warning(
                        f'Redirect target {targetPage} forms a redirect loop.')
                    break  # FIXME: doesn't work. edits twice!

                    if self.opt.delete:
                        # Delete the two redirects
                        # TODO: Check whether pages aren't vandalized
                        # and (maybe) do not have a version history
                        self.delete_redirect(targetPage,
                                             'redirect-remove-loop')
                        self.delete_redirect(redir, 'redirect-remove-loop')
                    break

                # redirect target found
                if targetPage.isStaticRedirect():
                    pywikibot.info('   Redirect target is STATICREDIRECT.')
                else:
                    newRedir = targetPage
                    continue

            oldText = redir.get(get_redirect=True)
            if self.is_repo and redir.namespace() == self.repo.item_namespace:
                redir = pywikibot.ItemPage(self.repo, redir.title())
                targetPage = pywikibot.ItemPage(self.repo, targetPage.title())
                pywikibot.info('Fixing double item redirect')
                redir.set_redirect_target(targetPage)
                break
            redir.set_redirect_target(targetPage, keep_section=True,
                                      save=False)
            summary = i18n.twtranslate(
                redir.site, 'redirect-fix-double',
                {'to': targetPage.title(as_link=True, allow_interwiki=False)},
                bot_prefix=True)
            self.userPut(redir, oldText, redir.text, summary=summary,
                         ignore_save_related_errors=True,
                         ignore_server_errors=True)
            break

    def fix_double_or_delete_broken_redirect(self) -> None:
        """Treat one broken or double redirect."""
        if self.current_page._redirect_type == 0:
            self.delete_1_broken_redirect()
        elif self.current_page._redirect_type != 1:
            self.fix_1_double_redirect()

    def treat(self, page) -> None:
        """Treat a page.

        :param page: Page to be treated.
        :type page: pywikibot.page.BasePage
        """
        if self.counter['read'] >= self.opt.limit:
            pywikibot.info(
                '\nNumber of pages reached the limit. Script terminated.')
            self.generator.close()
        super().treat(page)


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    options: Dict[str, Any] = {}
    gen_options: Dict[str, Any] = {}
    # what the bot should do (either resolve double redirs, or process broken
    # redirs)
    action = None
    source = set()
    unknown = []
    gen_factory = pagegenerators.GeneratorFactory()

    local_args = pywikibot.handle_args(args)
    shorts = {'do': 'double', 'br': 'broken'}
    for argument in local_args:
        arg, _, value = argument.partition(':')
        option = arg.partition('-')[2]
        # bot options
        if arg in shorts:
            action = shorts[arg]
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
        elif option == 'offset':
            gen_options[option] = int(value)
        elif option in ('start', 'until'):
            gen_options[option] = value
        elif option == 'limit':
            options['limit'] = gen_options['limit'] = int(value)
        elif gen_factory.handle_arg(argument):
            pass
        else:
            unknown.append(arg)

    problem = 'You can only use one of {} options.'.format(
        ' or '.join(source)) if len(source) > 1 else ''

    if action == 'both' and '-fullscan' in source:
        problem += (' You can only use either -fullscan together with '
                    "broken/double action or 'both' action")

    if suggest_help(additional_text=fill(problem),
                    unknown_parameters=unknown,
                    missing_action=not action):
        return

    gen = None
    if not gen_factory.gens:
        if gen_factory.namespaces:
            gen_options['namespaces'] = gen_factory.namespaces
        gen = RedirectGenerator(action, **gen_options)

    if gen_factory.gens \
       or action != 'both' and source not in ('-fullscan', '-xml'):
        gen = gen_factory.getCombinedGenerator(gen=gen)

    bot = RedirectRobot(action, generator=gen, **options)
    bot.run()


if __name__ == '__main__':
    main()
